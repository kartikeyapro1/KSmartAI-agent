# GenAI Agent — Milestone 6 (Upload + RAG + Ollama + Web UI)

FastAPI service with:
- Per-user **conversation memory** (last 8 turns, in RAM)
- **Local LLM via Ollama** (free, no cloud)
- **RAG**: answers grounded in your own docs (TXT/MD/PDF)
- **File upload** endpoint and **browser UI** (auto-reindex on upload)
- Clean **Pydantic** schemas + permissive **CORS** for local dev

---

## Stack
- Backend: **FastAPI** (Python)
- LLM: **Ollama** (default chat model: `llama3.1`)
- Embeddings: **`nomic-embed-text`** via Ollama
- UI: static HTML/JS served by FastAPI (`web/index.html`)
- Config: **.env** via `python-dotenv`

---


---

## Prerequisites
- Python **3.11+** (3.13 works for this project)
- **Ollama** running at `http://localhost:11434`
- Windows PowerShell (or macOS/Linux shell)

### Install Ollama (Windows PowerShell)
```powershell
winget install Ollama.Ollama
ollama pull llama3.1
ollama pull nomic-embed-text
```
---
### Setup and Run
``` powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```
---
### Create .env at the project root (copy from .env.example if present):
PROVIDER=ollama
OLLAMA_MODEL=llama3.1
EMBED_MODEL=nomic-embed-text
SYSTEM_PROMPT=You are a concise, helpful assistant. If unsure, say so.


---
### Start the API (from the repo root):
``` powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```
- OPEN:
- Web UI: http://127.0.0.1:8000/

- Docs (Swagger): http://127.0.0.1:8000/docs
---
### Using the web UI
- Reindex: rebuilds the RAG index from data/docs/

- Clear memory: clears your per-tab session (stored via localStorage)

- Upload: choose .txt/.md/.pdf files → Upload → auto-reindex

- Chat: ask questions; when context is used, source filenames appear as chips
---
### API Endpoints
- GET/HEALTH
- Returns({"status":"ok","provider":"ollama","model":"llama3.1"}
  )
- POST/CHAT
- Request({ "user_id": "kart", "message": "What degree does Kartikeya study?" }
  )
- RESPONSE({
  "reply": "…AI-grounded answer…",
  "history": [
  {"role":"user","content":"…"},
  {"role":"assistant","content":"…"}
  ],
  "sources": ["about-kart.txt"]
  }
  )
---
### Quick tests
### Health
GET http://127.0.0.1:8000/health

### Clear
POST http://127.0.0.1:8000/memory/kart/clear

### Reindex
POST http://127.0.0.1:8000/reindex

### Chat
POST http://127.0.0.1:8000/chat
Content-Type: application/json

- { "user_id": "kart", "message": "Explain APIs in one sentence." }
---
### Troubleshooting
- Site shows {"detail":"Not Found"} at /
- Ensure web/index.html exists at <repo-root>/web/index.html and the mount happens after app = FastAPI(...).
- Bullet-proof absolute path mount(from pathlib import Path
  ROOT = Path(__file__).resolve().parents[1]
  app.mount("/", StaticFiles(directory=str(ROOT / "web"), html=True), name="web")
  )
- Docs show an old milestone title
  You’re hitting an old server instance. Stop it and restart on a new port, then hard refresh (Ctrl+F5).
  Check http://127.0.0.1:8000/openapi.json → info.title should match.

- ollama-unreachable in /health
Start/verify Ollama: ollama serve (or run any ollama command to auto-start). Confirm: curl http://localhost:11434/api/tags.

- Timeout on first /chat
Warm the model once: ollama run llama3.1 (type hello, then Ctrl+C). Or switch to OLLAMA_MODEL=llama3.2:3b.

- /upload returns 422
Install and restart: pip install python-multipart.

- Opened web/index.html directly (file://) and the UI can’t call the API
Always use the server URL (http://127.0.0.1:8000/
).
---
### Security Notes
- Memory is in-process RAM (cleared on restart).

- Uploads are written under data/docs/ and reindexed immediately.

- Keep secrets out of Git: .env is in .gitignore; commit only .env.example.
---

### License
MIT © 2025 Kartikeya Sharma

