# PDF Q&A Chatbot

A simple RAG-based chatbot that answers questions from PDF documents.

## Setup

1. Create virtual environment:
```bash
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows PowerShell
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

4. Add PDF files to `data/pdfs/` directory

5. Run ingestion:
```bash
python src/ingest.py
```

## Project Status

Currently in **Phase 1**: PDF Ingestion & Vectorization

See `PROJECT_GUIDE.md` for full project documentation.
