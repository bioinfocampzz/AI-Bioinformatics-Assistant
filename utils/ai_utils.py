from __future__ import annotations

import os
from typing import Dict, List, Optional
import hashlib

import requests


SYSTEM_PROMPT = (
    "You are a bioinformatics expert and teacher. "
    "Explain concepts clearly, avoid hallucinations, and provide scientifically "
    "accurate answers in simple language. Keep responses concise but informative."
)


MODEL_CANDIDATES = [
    "google/gemini-2.0-flash-001",
    "google/gemini-2.0-flash-lite-001",
    "google/gemini-1.5-flash",
]

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Simple in-memory cache for responses
_response_cache: Dict[str, str] = {}
_cache_max_size = 100


def _get_cache_key(content: str) -> str:
    """Generate a cache key from content hash."""
    return hashlib.md5(content.encode()).hexdigest()[:12]


def _cache_get(key: str) -> Optional[str]:
    """Get cached response."""
    return _response_cache.get(key)


def _cache_set(key: str, value: str) -> None:
    """Set cached response with LRU eviction."""
    if len(_response_cache) >= _cache_max_size:
        # Remove oldest entry (simple FIFO for now)
        _response_cache.pop(next(iter(_response_cache)))
    _response_cache[key] = value


def _build_history_block(history: Optional[List[Dict[str, str]]], max_history: int = 3) -> str:
    """Build history block with optional truncation for large histories."""
    if not history:
        return "No prior chat history."

    # Use only most recent messages to reduce token count
    limited = history[-max_history:]
    lines = []
    for item in limited:
        role = item.get("role", "user").strip().lower()
        role_label = "User" if role == "user" else "Assistant"
        content = item.get("content", "").strip()
        
        # Truncate long messages
        if len(content) > 200:
            content = content[:197] + "..."
        
        if content:
            lines.append(f"{role_label}: {content}")

    return "\n".join(lines) if lines else "No prior chat history."


def _get_openrouter_api_key() -> str:
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if api_key:
        return api_key

    # Backward compatibility for older .env files where the OpenRouter key
    # was accidentally stored under GEMINI_API_KEY.
    legacy_key = os.getenv("GEMINI_API_KEY", "").strip()
    if legacy_key.startswith("sk-or-"):
        return legacy_key

    return ""


def _extract_message_text(raw_content) -> str:
    if isinstance(raw_content, str):
        return raw_content.strip()

    if isinstance(raw_content, list):
        parts: List[str] = []
        for item in raw_content:
            if isinstance(item, dict) and item.get("type") == "text":
                text = str(item.get("text", "")).strip()
                if text:
                    parts.append(text)
        return "\n".join(parts).strip()

    return ""


def _generate_text_via_openrouter(prompt: str, use_cache: bool = True) -> str:
    """Generate text with optional response caching."""
    
    # Check cache first
    if use_cache:
        cache_key = _get_cache_key(prompt)
        cached = _cache_get(cache_key)
        if cached:
            return cached
    else:
        cache_key = None
    
    api_key = _get_openrouter_api_key()
    if not api_key:
        return (
            "OpenRouter API key is missing. Set OPENROUTER_API_KEY in your "
            "environment to enable AI responses."
        )

    app_url = os.getenv("OPENROUTER_APP_URL", "http://localhost:8501")
    app_name = os.getenv("OPENROUTER_APP_NAME", "AI Bioinformatics Assistant")
    preferred_model = os.getenv("OPENROUTER_MODEL", "").strip()
    model_list = [preferred_model] if preferred_model else []
    model_list.extend([m for m in MODEL_CANDIDATES if m not in model_list])

    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": app_url,
        "X-Title": app_name,
        "Content-Type": "application/json",
    }

    last_error = ""
    for model in model_list:
        payload = {
            "model": model,
            "temperature": 0.3,
            "max_tokens": 500,  # Limit output tokens
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        }

        try:
            response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=90)
            if response.status_code >= 400:
                last_error = f"{response.status_code}: {response.text[:240]}"
                continue

            data = response.json()
            choices = data.get("choices", [])
            if not choices:
                last_error = "No choices returned by OpenRouter."
                continue

            raw_content = choices[0].get("message", {}).get("content", "")
            text = _extract_message_text(raw_content)
            if text:
                # Cache the result
                if use_cache and cache_key:
                    _cache_set(cache_key, text)
                return text
            last_error = "Empty content returned by OpenRouter."
        except Exception as exc:
            last_error = str(exc)

    return f"Error while contacting OpenRouter: {last_error or 'Unknown error'}"


def generate_chat_response(
    user_query: str,
    history: Optional[List[Dict[str, str]]] = None,
    analysis_context: Optional[Dict] = None,
) -> str:
    """Generate chat response with optimized prompt size."""
    # Limit history to reduce context
    history_block = _build_history_block(history, max_history=2)
    analysis_block = "No sequence analysis context provided."

    if analysis_context:
        # Only include most relevant analysis fields
        relevant_context = {
            "number_of_sequences": analysis_context.get("number_of_sequences"),
            "total_length": analysis_context.get("total_length"),
            "average_length": analysis_context.get("average_length"),
            "overall_gc_content": analysis_context.get("overall_gc_content"),
            "files_analyzed": analysis_context.get("files_analyzed"),
        }
        analysis_block = (
            "Sequence analysis summary:\n"
            f"{relevant_context}"
        )

    # Truncate query if too long
    query_display = user_query
    if len(user_query) > 300:
        query_display = user_query[:297] + "..."

    prompt = (
        "Answer the user in a teaching style suitable for students.\n\n"
        f"Recent Conversation:\n{history_block}\n\n"
        f"Analysis Context:\n{analysis_block}\n\n"
        f"User Question:\n{query_display}\n"
    )
    return _generate_text_via_openrouter(prompt, use_cache=True)


def explain_analysis(analysis_summary: Dict) -> str:
    """Explain analysis with optimized context."""
    # Only include top-level summary fields
    compact_summary = {
        "number_of_sequences": analysis_summary.get("number_of_sequences"),
        "total_length": analysis_summary.get("total_length"),
        "average_length": analysis_summary.get("average_length"),
        "overall_gc_content": analysis_summary.get("overall_gc_content"),
    }
    
    # Add first 3 sequences only if available
    sequences = analysis_summary.get("first_five_sequences", [])[:3]
    if sequences:
        compact_summary["sample_sequences"] = sequences
    
    prompt = (
        "You will receive summarized sequence statistics. "
        "Provide a short biological interpretation for students. "
        "Mention possible implications of GC content and sequence length distribution.\n\n"
        f"Summary:\n{compact_summary}"
    )
    return _generate_text_via_openrouter(prompt, use_cache=True)
