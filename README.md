# GenAI Agent — Milestone 2
FastAPI service with:
- Per-user **conversation memory** (keeps last 8 turns in RAM).
- Clean Pydantic **schemas** and **CORS** enabled (ready for a frontend).
- Endpoints: `/health`, `/chat`, `/memory/{user_id}/clear`.

## Run locally
```bash
# from project root
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
