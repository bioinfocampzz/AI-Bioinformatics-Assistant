from __future__ import annotations

from typing import Dict, List, Optional
import hashlib
import time

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from utils.ai_utils import explain_analysis, generate_chat_response
from utils.analysis import summarize_sequences
from utils.parser import parse_sequences


app = FastAPI(title="AI Bioinformatics Assistant API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
MAX_RECORDS_DETAILED = 10000  # Max records to analyze in detail
CACHE_MAX_SIZE = 50
CACHE_EXPIRY = 3600  # 1 hour

# Simple cache for analysis results
_analysis_cache: Dict[str, tuple[Dict, float]] = {}


def _get_cache_key(content: str, file_name: str) -> str:
    """Generate cache key from content hash."""
    combined = f"{file_name}:{content[:1000]}"
    return hashlib.md5(combined.encode()).hexdigest()[:16]


def _cache_get(key: str) -> Optional[Dict]:
    """Get cached analysis result."""
    if key not in _analysis_cache:
        return None
    
    result, timestamp = _analysis_cache[key]
    if time.time() - timestamp > CACHE_EXPIRY:
        del _analysis_cache[key]
        return None
    
    return result


def _cache_set(key: str, value: Dict) -> None:
    """Set cached analysis with LRU eviction."""
    if len(_analysis_cache) >= CACHE_MAX_SIZE:
        # Remove oldest entry
        oldest_key = min(_analysis_cache.keys(), key=lambda k: _analysis_cache[k][1])
        del _analysis_cache[oldest_key]
    
    _analysis_cache[key] = (value, time.time())


class ChatMessage(BaseModel):
    role: str = Field(..., description="user or assistant")
    content: str


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    history: List[ChatMessage] = Field(default_factory=list, max_length=20)
    analysis_context: Optional[Dict] = None


class AnalyzeRequest(BaseModel):
    sequence_text: str = Field(..., min_length=1, max_length=102400000)  # 100MB
    file_name: str = ""


@app.get("/health")
def health_check() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/chat")
def chat(request: ChatRequest) -> Dict[str, str]:
    """Handle chat requests with optimized history."""
    history_dicts = [{"role": msg.role, "content": msg.content} for msg in request.history]
    response_text = generate_chat_response(
        user_query=request.query,
        history=history_dicts,
        analysis_context=request.analysis_context,
    )
    return {"response": response_text}


@app.post("/analyze")
def analyze(request: AnalyzeRequest) -> Dict:
    """Analyze sequences with caching and file size limits."""
    try:
        # Validate file size
        file_size_mb = len(request.sequence_text) / (1024 * 1024)
        if len(request.sequence_text) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File size {file_size_mb:.1f}MB exceeds limit of {MAX_FILE_SIZE / 1024 / 1024:.0f}MB"
            )
        
        # Check cache first
        cache_key = _get_cache_key(request.sequence_text, request.file_name)
        cached_result = _cache_get(cache_key)
        if cached_result:
            cached_result["_from_cache"] = True
            return cached_result
        
        # Parse sequences with limits
        records = parse_sequences(
            request.sequence_text,
            request.file_name,
            max_records=None,  # No hard limit, but detailed analysis has limit
            max_file_size=MAX_FILE_SIZE
        )

        # Summarize with optional ORF computation
        summary = summarize_sequences(
            records,
            compute_orfs=False,  # Skip expensive ORF computation by default
            limit_sequences=MAX_RECORDS_DETAILED
        )

        # Only get AI interpretation for reasonable-sized datasets
        ai_interpretation = ""
        if len(records) <= 1000:
            # Only summarized data is shared with Gemini, not raw sequence strings.
            ai_interpretation = explain_analysis(
                {
                    "number_of_sequences": summary["number_of_sequences"],
                    "total_length": summary["total_length"],
                    "average_length": summary["average_length"],
                    "overall_gc_content": summary["overall_gc_content"],
                    "first_five_sequences": summary["sequences"][:5],
                }
            )

        result = {
            "file_name": request.file_name,
            "summary": summary,
            "ai_interpretation": ai_interpretation,
            "file_size_mb": round(file_size_mb, 2),
            "processing_stats": {
                "total_records": len(records),
                "records_detailed": min(len(records), MAX_RECORDS_DETAILED),
            }
        }
        
        # Cache the result
        _cache_set(cache_key, result)
        
        return result
        
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unexpected server error: {exc}") from exc
