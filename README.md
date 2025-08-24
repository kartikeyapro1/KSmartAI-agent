# GenAI Agent — Milestone 4: RAG with Ollama embeddings + reindex

FastAPI service with:
- Per-user **conversation memory** (last 8 turns, in RAM)
- **Ollama** local LLM backend (no cloud, free)
- Clean **Pydantic** schemas + **CORS** (ready for a frontend)
- Endpoints: `/health`, `/chat`, `/memory/{user_id}/clear`

> Next milestone adds **RAG** (answer from your own docs) using local embeddings.

---

## Stack
- Backend: **FastAPI** (Python)
- LLM: **Ollama** (local) — default model: `llama3.1`
- Env/config: `.env` via `python-dotenv`

---

## Prerequisites
- Python **3.11+** (3.13 works on this project)
- Windows (PowerShell) or macOS/Linux
- **Ollama** installed and running at `http://localhost:11434`

### Install Ollama (Windows Powershell)
```powershell
winget install Ollama.Ollama

```
### Pull models (chat+embeddings)
```powershell
ollama pull llama3.1
ollama pull nomic-embed-text
```
### Setup and Run
```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# .env in project root
# PROVIDER=ollama
# OLLAMA_MODEL=llama3.1
# EMBED_MODEL=nomic-embed-text
# SYSTEM_PROMPT=You are a concise, helpful assistant. If unsure, say so.

.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
