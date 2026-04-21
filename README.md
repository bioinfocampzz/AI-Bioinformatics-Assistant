# AI Bioinformatics Assistant

AI-powered bioinformatics tutor and sequence analyzer using Streamlit + FastAPI + OpenRouter.

## Project Structure

- `frontend/app.py` - Streamlit chatbot interface
- `backend/main.py` - FastAPI backend APIs
- `utils/parser.py` - FASTA/FASTQ parsing utilities
- `utils/analysis.py` - Sequence analysis (length, GC, optional ORF/motif helpers)
- `utils/ai_utils.py` - OpenRouter integration and prompt building
- `example_data/sample.fasta` - Example input file

## Features

- Concept Q&A for bioinformatics topics
- Sequence analysis for FASTA/FASTQ-like inputs
- GC content and sequence length summary
- AI interpretation of summarized sequence statistics
- Chat memory using recent conversation context

## Setup

1. Create and activate virtual environment (recommended):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Configure environment variables:

```powershell
copy .env.example .env
```

Then set your OpenRouter API key inside `.env`:

```env
OPENROUTER_API_KEY=
OPENROUTER_MODEL=
BACKEND_URL=http://127.0.0.1:8000
```

## Run the Application

1. Start FastAPI backend:

```powershell
uvicorn backend.main:app --reload
```

2. In a second terminal, start Streamlit frontend:

```powershell
streamlit run frontend/app.py
```

3. Open the Streamlit URL shown in terminal (typically `http://localhost:8501`).

## API Endpoints

- `POST /chat`
  - Input: user query + optional chat history + optional analysis context
  - Output: AI response text

- `POST /analyze`
  - Input: sequence text and file name
  - Output: sequence statistics + AI interpretation

- `GET /health`
  - Output: health status

## Notes

- Large raw sequences are not sent directly to the LLM.
- Only summarized analysis statistics are sent for interpretation.
- Invalid FASTA/FASTQ files are handled with descriptive errors.
