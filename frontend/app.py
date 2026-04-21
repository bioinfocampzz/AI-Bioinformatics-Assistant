from __future__ import annotations

import os
from typing import Dict, List

import requests
import streamlit as st
from dotenv import load_dotenv


load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
SUPPORTED_EXTENSIONS = ["fasta", "fa", "fna", "fastq", "fq", "txt"]


st.set_page_config(
    page_title="AI Bioinformatics Assistant", 
    page_icon="🧬", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=IBM+Plex+Mono:wght@400;600&display=swap');

    :root {
        --bg: #0f1419;
        --panel: #1a1f27;
        --panel-light: #252d38;
        --ink: #e8eef5;
        --muted: #8b94a5;
        --accent: #00d9ff;
        --accent-soft: #001a24;
        --accent-glow: rgba(0, 217, 255, 0.3);
        --border: #2d3748;
        --success: #10b981;
        --warning: #f59e0b;
        --danger: #ef4444;
    }

    html, body, [class*="css"] {
        font-family: 'Space Grotesk', sans-serif;
        color: var(--ink);
        background:
            radial-gradient(circle at 10% 50%, rgba(0, 217, 255, 0.08) 0%, transparent 40%),
            radial-gradient(circle at 90% 80%, rgba(59, 130, 246, 0.08) 0%, transparent 40%),
            var(--bg);
        background-attachment: fixed;
    }

    .stApp {
        background: transparent;
    }

    .bio-card {
        border: 1.5px solid var(--border);
        border-radius: 16px;
        padding: 1.5rem;
        background: linear-gradient(135deg, var(--panel) 0%, var(--panel-light) 100%);
        box-shadow: 0 8px 32px rgba(0, 217, 255, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }

    .bio-card:hover {
        border-color: var(--accent);
        box-shadow: 0 12px 48px rgba(0, 217, 255, 0.15), inset 0 1px 0 rgba(255, 255, 255, 0.05);
    }

    .bio-title {
        letter-spacing: 0.02em;
        font-weight: 700;
        color: var(--accent);
    }

    .quick-start-section {
        background: linear-gradient(135deg, rgba(0, 217, 255, 0.1) 0%, rgba(59, 130, 246, 0.1) 100%);
        border: 1.5px solid var(--border);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        backdrop-filter: blur(10px);
    }

    .quick-start-item {
        background: var(--panel);
        border-left: 3px solid var(--accent);
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 8px;
        transition: all 0.2s ease;
    }

    .quick-start-item:hover {
        transform: translateX(4px);
        border-left-color: var(--accent);
        box-shadow: 0 4px 16px rgba(0, 217, 255, 0.1);
    }

    .step-badge {
        display: inline-block;
        background: var(--accent);
        color: var(--bg);
        font-weight: 700;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        margin-right: 0.5rem;
    }

    .mono {
        font-family: 'IBM Plex Mono', monospace;
        background: var(--accent-soft);
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        color: var(--accent);
    }

    .header-glow {
        background: linear-gradient(135deg, var(--accent) 0%, #3b82f6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .stats-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 1rem;
        margin: 1rem 0;
    }

    .stat-box {
        background: var(--panel);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
    }

    .stat-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--accent);
    }

    .stat-label {
        font-size: 0.85rem;
        color: var(--muted);
        margin-top: 0.25rem;
    }

    .example-box {
        background: var(--accent-soft);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }

    .stButton>button {
        background: linear-gradient(135deg, var(--accent) 0%, #3b82f6 100%);
        color: var(--bg) !important;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.75rem 1.5rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 16px rgba(0, 217, 255, 0.2);
    }

    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 24px rgba(0, 217, 255, 0.3);
    }

    .sidebar-title {
        color: var(--accent);
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-size: 0.9rem;
        margin: 1.5rem 0 1rem 0;
    }

    .tab-indicator {
        color: var(--accent);
        font-weight: 700;
    }

    .guide-container {
        background: linear-gradient(135deg, rgba(0, 217, 255, 0.15) 0%, rgba(59, 130, 246, 0.15) 100%);
        border: 1.5px solid var(--accent);
        border-radius: 14px;
        padding: 2rem;
        margin: 1.5rem 0;
        backdrop-filter: blur(15px);
        position: relative;
        overflow: hidden;
    }

    .guide-container::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, var(--accent), transparent);
    }

    .guide-step-card {
        background: linear-gradient(135deg, rgba(26, 31, 39, 0.8) 0%, rgba(37, 45, 56, 0.8) 100%);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        backdrop-filter: blur(10px);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }

    .guide-step-card::before {
        content: '';
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        width: 4px;
        background: linear-gradient(180deg, var(--accent) 0%, #3b82f6 100%);
    }

    .guide-step-card:hover {
        transform: translateX(6px);
        border-color: var(--accent);
        box-shadow: 0 8px 24px rgba(0, 217, 255, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.05);
    }

    .step-number {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 40px;
        height: 40px;
        background: linear-gradient(135deg, var(--accent) 0%, #3b82f6 100%);
        color: var(--bg);
        border-radius: 50%;
        font-weight: 700;
        font-size: 1.2rem;
        margin-right: 1rem;
        box-shadow: 0 4px 16px rgba(0, 217, 255, 0.3);
    }

    .step-title {
        font-weight: 700;
        color: var(--accent);
        font-size: 1.1rem;
        margin-bottom: 0.5rem;
    }

    .step-description {
        color: var(--muted);
        line-height: 1.6;
        margin-left: 3rem;
    }

    .feature-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin: 1.5rem 0;
    }

    .feature-box {
        background: linear-gradient(135deg, rgba(26, 31, 39, 0.6) 0%, rgba(37, 45, 56, 0.6) 100%);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 1.2rem;
        text-align: center;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }

    .feature-box:hover {
        border-color: var(--accent);
        box-shadow: 0 6px 20px rgba(0, 217, 255, 0.15);
        transform: translateY(-4px);
    }

    .feature-icon {
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }

    .feature-title {
        color: var(--accent);
        font-weight: 600;
        margin-bottom: 0.5rem;
    }

    .feature-text {
        color: var(--muted);
        font-size: 0.9rem;
    }

    .guide-title {
        color: var(--accent);
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 1rem;
    }

    .guide-subtitle {
        color: var(--muted);
        font-size: 0.95rem;
        margin-bottom: 1.5rem;
    }

    .divider-accent {
        height: 2px;
        background: linear-gradient(90deg, var(--accent), transparent);
        margin: 1.5rem 0;
    }

    .info-box {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(6, 182, 212, 0.1) 100%);
        border-left: 3px solid var(--success);
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }

    .info-text {
        color: var(--ink);
        font-size: 0.95rem;
    }

    .enhancement-badge {
        display: inline-block;
        background: linear-gradient(135deg, var(--accent) 0%, #3b82f6 100%);
        color: var(--bg);
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        box-shadow: 0 2px 8px rgba(0, 217, 255, 0.3);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


if "chat_history" not in st.session_state:
    st.session_state.chat_history: List[Dict[str, str]] = []

if "analysis_results" not in st.session_state:
    st.session_state.analysis_results: List[Dict] = []

if "show_quick_start" not in st.session_state:
    st.session_state.show_quick_start = True

# Optimization: Cache file data to avoid re-uploading
if "last_file_hash" not in st.session_state:
    st.session_state.last_file_hash = None

if "cached_analysis" not in st.session_state:
    st.session_state.cached_analysis: Dict = {}


# Header section with gradient
st.markdown(
    """
    <div style="text-align: center; padding: 3rem 0 1.5rem 0;">
        <div style="margin-bottom: 1rem;">
            <span style="font-size: 3rem;">🧬</span>
        </div>
        <h1 style="margin: 0; font-size: 2.8rem; letter-spacing: 0.01em;">
            <span class="header-glow">AI Bioinformatics Assistant</span>
        </h1>
        <p style="color: var(--muted); margin-top: 1rem; font-size: 1.15rem; letter-spacing: 0.01em; font-weight: 500;">
            Intelligent sequence analysis powered by Gemini AI
        </p>
        <div style="display: flex; justify-content: center; gap: 1.5rem; margin-top: 1.5rem; flex-wrap: wrap;">
            <span class="enhancement-badge">Advanced Analytics</span>
            <span class="enhancement-badge">Real-time Processing</span>
            <span class="enhancement-badge">Multi-format Support</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div class='divider-accent' style='margin: 2rem 0;'></div>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("<div class='sidebar-title'>📤 Sequence Input</div>", unsafe_allow_html=True)
    uploaded_files = st.file_uploader(
        "Upload FASTA/FASTQ files",
        type=SUPPORTED_EXTENSIONS,
        accept_multiple_files=True,
        help="Supported formats: FASTA (.fa, .fasta, .fna), FASTQ (.fq, .fastq), or TXT"
    )

    st.markdown("<div class='sidebar-title'>📚 Example Formats</div>", unsafe_allow_html=True)
    with st.expander("View examples", expanded=False):
        st.markdown("""
        **FASTA Format:**
        ```
        >sequence_id_1
        ATGCGTACGTACGTA
        >sequence_id_2
        GCTAGCTAGCTAGCT
        ```
        
        **FASTQ Format:**
        ```
        @read1
        ACGTACGTACGTACGT
        +
        IIIIIIIIIIIIIIII
        ```
        """)

    st.markdown("<div class='sidebar-title'>⚡ Quick Start</div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📖 Show Guide", use_container_width=True):
            st.session_state.show_quick_start = True
    with col2:
        if st.button("✕ Hide Guide", use_container_width=True):
            st.session_state.show_quick_start = False

    if uploaded_files:
        st.markdown("<div class='sidebar-title'>✅ Uploaded Files</div>", unsafe_allow_html=True)
        for idx, file in enumerate(uploaded_files, 1):
            size_kb = file.size / 1024
            st.markdown(
                f"<div class='quick-start-item'><strong>{idx}. {file.name}</strong><br><small>{size_kb:.1f} KB</small></div>",
                unsafe_allow_html=True
            )


def call_backend_chat(query: str, history: List[Dict[str, str]], analysis_context: Dict | None) -> str:
    payload = {
        "query": query,
        "history": history[-5:],
        "analysis_context": analysis_context,
    }
    response = requests.post(f"{BACKEND_URL}/chat", json=payload, timeout=90)
    response.raise_for_status()
    data = response.json()
    return data.get("response", "No response generated.")


def call_backend_analyze(sequence_text: str, file_name: str) -> Dict:
    payload = {"sequence_text": sequence_text, "file_name": file_name}
    response = requests.post(f"{BACKEND_URL}/analyze", json=payload, timeout=120)
    response.raise_for_status()
    return response.json()


def build_analysis_context(results: List[Dict]) -> Dict:
    if not results:
        return {}

    aggregate = {
        "files_analyzed": len(results),
        "file_summaries": [],
    }

    for item in results:
        summary = item.get("summary", {})
        aggregate["file_summaries"].append(
            {
                "file": item.get("file_name", "unknown"),
                "number_of_sequences": summary.get("number_of_sequences", 0),
                "total_length": summary.get("total_length", 0),
                "average_length": summary.get("average_length", 0),
                "overall_gc_content": summary.get("overall_gc_content", 0),
            }
        )

    return aggregate


col_left, col_right = st.columns([2, 1], gap="large")

# Quick Start Guide - Using Streamlit components
if st.session_state.show_quick_start:
    st.markdown(
        """
        <div class="guide-container">
            <div class="guide-title">🚀 Quick Start Guide</div>
            <div class="guide-subtitle">Get started in 3 simple steps to analyze your bioinformatics data</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Step 1
    col1, col2 = st.columns([0.15, 0.85], gap="small")
    with col1:
        st.markdown("<div style='text-align: center; margin-top: 0.5rem;'>📤</div>", unsafe_allow_html=True)
    with col2:
        st.markdown(
            """
            <div class="guide-step-card">
                <div style="display: flex; align-items: flex-start;">
                    <div class="step-number">1</div>
                    <div style="flex: 1;">
                        <div class="step-title">Upload Your Sequences</div>
                        <div class="step-description">
                            Navigate to the sidebar and upload your FASTA or FASTQ files. 
                            You can upload multiple files at once. Supported formats include:
                            <ul style="margin: 0.5rem 0 0 0; color: var(--muted);">
                                <li>FASTA (.fa, .fasta, .fna)</li>
                                <li>FASTQ (.fq, .fastq)</li>
                                <li>Plain text (.txt)</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    # Step 2
    col1, col2 = st.columns([0.15, 0.85], gap="small")
    with col1:
        st.markdown("<div style='text-align: center; margin-top: 0.5rem;'>🔍</div>", unsafe_allow_html=True)
    with col2:
        st.markdown(
            """
            <div class="guide-step-card">
                <div style="display: flex; align-items: flex-start;">
                    <div class="step-number">2</div>
                    <div style="flex: 1;">
                        <div class="step-title">Analyze Your Data</div>
                        <div class="step-description">
                            Click the "🔍 Analyze Sequences" button on the right panel.
                            The system will compute comprehensive statistics including:
                            <ul style="margin: 0.5rem 0 0 0; color: var(--muted);">
                                <li>Sequence count and lengths</li>
                                <li>GC content percentage</li>
                                <li>AI-powered interpretations</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    # Step 3
    col1, col2 = st.columns([0.15, 0.85], gap="small")
    with col1:
        st.markdown("<div style='text-align: center; margin-top: 0.5rem;'>💬</div>", unsafe_allow_html=True)
    with col2:
        st.markdown(
            """
            <div class="guide-step-card">
                <div style="display: flex; align-items: flex-start;">
                    <div class="step-number">3</div>
                    <div style="flex: 1;">
                        <div class="step-title">Ask Questions & Explore</div>
                        <div class="step-description">
                            Chat with the AI assistant on the left panel. Ask about sequence concepts,
                            interpretations, biological significance, and more. The AI has full context
                            of your analyzed data.
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    # Key Features Grid
    st.markdown("<div class='divider-accent'></div>", unsafe_allow_html=True)
    
    st.markdown(
        """
        <div style="margin: 2rem 0; padding: 0 0.5rem;">
            <div style="color: var(--muted); font-size: 0.9rem; margin-bottom: 1rem; text-transform: uppercase; letter-spacing: 0.05em;">Key Features</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    col1, col2, col3 = st.columns(3, gap="small")
    
    with col1:
        st.markdown(
            """
            <div class="feature-box">
                <div class="feature-icon">🧬</div>
                <div class="feature-title">Multi-Format</div>
                <div class="feature-text">Support for FASTA, FASTQ, and text files</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    with col2:
        st.markdown(
            """
            <div class="feature-box">
                <div class="feature-icon">🤖</div>
                <div class="feature-title">AI-Powered</div>
                <div class="feature-text">Gemini AI for intelligent analysis & insights</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    with col3:
        st.markdown(
            """
            <div class="feature-box">
                <div class="feature-icon">📊</div>
                <div class="feature-title">Real-time Stats</div>
                <div class="feature-text">Instant sequence metrics and analysis</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    # Tips section
    st.markdown(
        """
        <div class="info-box">
            <strong style="color: var(--success);">💡 Pro Tip:</strong>
            <p class="info-text" style="margin: 0.5rem 0 0 0;">
                Analyze your sequences first to provide context for better AI insights. 
                The assistant can reference specific data from your analysis to give more accurate interpretations.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    st.divider()

with col_right:
    st.markdown("<div class='bio-card'>", unsafe_allow_html=True)
    st.markdown("<h3 class='bio-title'>🔬 Sequence Analysis Hub</h3>", unsafe_allow_html=True)
    
    st.markdown(
        """
        <div style="color: var(--muted); font-size: 0.9rem; margin-bottom: 1rem;">
            Upload files and click analyze to get instant insights
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("🔍 Analyze Sequences", use_container_width=True, key="analyze_btn"):
        if not uploaded_files:
            st.warning("📁 Please upload at least one file before analysis.")
        else:
            st.session_state.analysis_results = []
            with st.spinner("🔄 Analyzing uploaded sequence files..."):
                for file in uploaded_files:
                    try:
                        text = file.getvalue().decode("utf-8", errors="ignore")
                        result = call_backend_analyze(text, file.name)
                        st.session_state.analysis_results.append(result)
                    except requests.HTTPError as http_err:
                        detail = ""
                        try:
                            detail = http_err.response.json().get("detail", "")
                        except Exception:
                            detail = str(http_err)
                        st.error(f"❌ Failed to analyze {file.name}: {detail}")
                    except Exception as exc:
                        st.error(f"❌ Failed to analyze {file.name}: {exc}")
            
            if st.session_state.analysis_results:
                st.success("✅ Analysis complete!")

    if st.session_state.analysis_results:
        st.markdown(
            """
            <div style="margin: 1.5rem 0; padding-top: 1.5rem; border-top: 1px solid var(--border);">
                <div style="color: var(--accent); font-weight: 600; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 1rem;">
                    Analysis Results
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        for item in st.session_state.analysis_results:
            file_name = item.get("file_name", "Unknown file")
            summary = item.get("summary", {})
            
            with st.expander(f"📊 {file_name}", expanded=False):
                # Stats Grid with enhanced styling
                st.markdown(
                    """
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1.5rem;">
                    """,
                    unsafe_allow_html=True,
                )
                
                # Stat 1
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(
                        f"""
                        <div class="stat-box">
                            <div class="stat-value">{summary.get('number_of_sequences', 0)}</div>
                            <div class="stat-label">Sequences</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                with col2:
                    st.markdown(
                        f"""
                        <div class="stat-box">
                            <div class="stat-value">{summary.get('overall_gc_content', 0)}%</div>
                            <div class="stat-label">GC Content</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(
                        f"""
                        <div class="stat-box">
                            <div class="stat-value">{summary.get('total_length', 0):,}</div>
                            <div class="stat-label">Total Length</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                with col2:
                    st.markdown(
                        f"""
                        <div class="stat-box">
                            <div class="stat-value">{summary.get('average_length', 0):.0f}</div>
                            <div class="stat-label">Avg Length</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                seq_rows = summary.get("sequences", [])
                total_seqs_in_result = summary.get("sequences_in_detail", len(seq_rows))
                
                if seq_rows:
                    st.markdown(
                        """
                        <div style="margin-top: 1.5rem; color: var(--accent); font-weight: 600; font-size: 0.9rem;">
                            📋 Sequence Details
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    
                    # Show pagination info if large dataset
                    if total_seqs_in_result < summary.get('number_of_sequences', 0):
                        st.info(
                            f"Showing first {total_seqs_in_result} of {summary.get('number_of_sequences', 0)} sequences. "
                            "Full statistics computed for all sequences."
                        )
                    
                    # Lazy load: Use pagination for large datasets
                    page_size = 100
                    num_pages = (len(seq_rows) + page_size - 1) // page_size
                    
                    if num_pages > 1:
                        page = st.slider(
                            "Page",
                            1,
                            num_pages,
                            1,
                            key=f"page_{file_name}"
                        )
                        start_idx = (page - 1) * page_size
                        end_idx = min(start_idx + page_size, len(seq_rows))
                        st.dataframe(
                            seq_rows[start_idx:end_idx],
                            use_container_width=True,
                            hide_index=True
                        )
                        st.caption(f"Showing {start_idx + 1} to {end_idx} of {len(seq_rows)}")
                    else:
                        st.dataframe(seq_rows, use_container_width=True, hide_index=True)

                ai_text = item.get("ai_interpretation", "")
                if ai_text:
                    with st.expander("🤖 AI Interpretation", expanded=False):
                        st.markdown(
                            f"""
                            <div style="background: rgba(0, 217, 255, 0.05); border-left: 3px solid var(--accent); padding: 1rem; border-radius: 6px; color: var(--ink);">
                                {ai_text}
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                
                # Show processing stats if available
                stats = item.get("processing_stats", {})
                if stats:
                    st.caption(
                        f"Processing: {stats.get('total_records', 'N/A')} total records, "
                        f"{stats.get('records_detailed', 'N/A')} detailed"
                    )

    st.markdown("</div>", unsafe_allow_html=True)

with col_left:
    st.markdown("<h3 class='bio-title'>💬 Intelligent Chat Assistant</h3>", unsafe_allow_html=True)
    
    st.markdown(
        """
        <div style="color: var(--muted); font-size: 0.9rem; margin-bottom: 1rem;">
            Ask questions about your sequences and bioinformatics concepts
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Chat history display with custom styling
    chat_container = st.container(border=True)
    with chat_container:
        st.markdown(
            """
            <style>
            .chat-message-wrapper {
                margin-bottom: 1rem;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        
        if not st.session_state.chat_history:
            st.markdown(
                """
                <div style="text-align: center; padding: 2rem 1rem; color: var(--muted);">
                    <div style="font-size: 2rem; margin-bottom: 1rem;">💭</div>
                    <p>No messages yet. Start a conversation!</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            for message in st.session_state.chat_history:
                avatar = "🤖" if message["role"] == "assistant" else "👤"
                with st.chat_message(message["role"], avatar=avatar):
                    st.markdown(
                        f"""
                        <div style="background: linear-gradient(135deg, rgba(26, 31, 39, 0.5) 0%, rgba(37, 45, 56, 0.5) 100%); 
                                    border: 1px solid var(--border); 
                                    border-radius: 8px; 
                                    padding: 1rem; 
                                    backdrop-filter: blur(10px);">
                            {message["content"]}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

    # Chat input
    user_prompt = st.chat_input("Ask a question about sequences or bioinformatics...", key="chat_input")
    if user_prompt:
        st.session_state.chat_history.append({"role": "user", "content": user_prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(
                f"""
                <div style="background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(0, 217, 255, 0.1) 100%); 
                            border: 1px solid var(--border); 
                            border-radius: 8px; 
                            padding: 1rem; 
                            backdrop-filter: blur(10px);">
                    {user_prompt}
                </div>
                """,
                unsafe_allow_html=True,
            )

        analysis_context = build_analysis_context(st.session_state.analysis_results)

        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("🧠 Thinking with Gemini..."):
                try:
                    assistant_text = call_backend_chat(
                        query=user_prompt,
                        history=st.session_state.chat_history,
                        analysis_context=analysis_context if analysis_context else None,
                    )
                except requests.HTTPError as http_err:
                    assistant_text = f"❌ Request failed: {http_err}"
                except Exception as exc:
                    assistant_text = f"❌ Could not contact backend: {exc}"

                st.markdown(
                    f"""
                    <div style="background: linear-gradient(135deg, rgba(0, 217, 255, 0.1) 0%, rgba(16, 185, 129, 0.1) 100%); 
                                border: 1px solid var(--border); 
                                border-radius: 8px; 
                                padding: 1rem; 
                                backdrop-filter: blur(10px);">
                        {assistant_text}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.session_state.chat_history.append({"role": "assistant", "content": assistant_text})
        st.rerun()
