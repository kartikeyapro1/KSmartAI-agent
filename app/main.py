import os
from pathlib import Path
from typing import List
from uuid import uuid4

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app import rag
from app.memory import add_turn, get_history, clear
from app.schemas import ChatRequest, ChatResponse, Message

load_dotenv()

PROVIDER = os.getenv("PROVIDER", "ollama").lower()
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")
SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT", "You are a helpful assistant.")

app = FastAPI(title="KSmartAI Agent — Upload + RAG + Ollama")


# CORS (permissive for local dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- RAG docs dir
DOCS_DIR = Path("data/docs")
DOCS_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_EXTS = {".txt", ".md", ".pdf"}

import os
import requests

CI = os.getenv("CI") == "true"  # GitHub Actions sets CI=true

@app.get("/health")
def health():
    out = {
        "status": "ok",           # app is up
        "provider": PROVIDER,
        "model": OLLAMA_MODEL,
    }
    # Only probe Ollama locally (CI has no daemon)
    if PROVIDER == "ollama" and not CI:
        try:
            r = requests.get("http://localhost:11434/api/tags", timeout=2)
            r.raise_for_status()
            out["ollama"] = "ok"
        except Exception:
            out["ollama"] = "unreachable"
    return out


@app.post("/memory/{user_id}/clear")
def clear_memory(user_id: str):
    clear(user_id)
    return {"ok": True, "message": f"memory cleared for {user_id}"}

@app.post("/reindex")
def reindex():
    info = rag.init_or_rebuild()
    return {"ok": True, "index": info}

@app.post("/upload")
async def upload(files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    saved = []
    for f in files:
        ext = Path(f.filename).suffix.lower()
        if ext not in ALLOWED_EXTS:
            raise HTTPException(status_code=415, detail=f"Unsupported file type: {ext}")

        name = Path(f.filename).name or f"upload-{uuid4().hex}{ext}"
        path = DOCS_DIR / name

        data = await f.read()
        try:
            path.write_bytes(data)
            saved.append(name)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save {name}: {type(e).__name__}")

    info = rag.init_or_rebuild()
    return {"ok": True, "saved": saved, "index": info}

def _call_ollama(messages):
    r = requests.post(
        "http://localhost:11434/api/chat",
        json={"model": OLLAMA_MODEL, "messages": messages, "stream": False},
        timeout=600,
    )
    r.raise_for_status()
    return r.json()["message"]["content"].strip()

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    user_msg = req.message

    # Save user turn
    add_turn(req.user_id, "user", user_msg)

    # RAG search
    hits = rag.search(user_msg, k=4)
    context_blocks = [f"[{src}] {txt}" for (txt, src) in hits]
    sources = list(dict.fromkeys([src for (_, src) in hits])) or None

    # Strict grounded mode: refuse if no context
    if req.grounded_only and not hits:
        reply = "I don’t have that in your documents yet. Try uploading a file or disable grounded-only mode."
        add_turn(req.user_id, "assistant", reply)
        hist_msgs = [Message(role=r, content=c) for r, c in get_history(req.user_id)]
        return ChatResponse(reply=reply, history=hist_msgs, sources=None)

    # Build messages (system + CONTEXT + memory + current user)
    base_rules = (
        "You have access to a CONTEXT block with snippets from the user's documents.\n"
        "If the answer is in CONTEXT, use it and cite the file names.\n"
        "If the answer isn't in CONTEXT, say you don't know.\n"
        "Be concise."
    )
    if req.grounded_only:
        base_rules += "\nAnswer strictly from CONTEXT; if unsure, reply: 'I don't know based on the docs.'"

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": base_rules},
    ]
    if context_blocks:
        messages.append({"role": "system", "content": "CONTEXT:\n" + "\n\n".join(context_blocks)})

    for role, content in get_history(req.user_id):
        if role in ("user", "assistant"):
            messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": user_msg})

    # Guardrail: trim prompt size
    MAX_CHARS = 12000
    total, trimmed = 0, []
    for m in reversed(messages):
        c = len(m["content"])
        if total + c <= MAX_CHARS or m["role"] == "system":
            trimmed.append(m); total += c
    messages = list(reversed(trimmed))

    # Call local LLM
    try:
        reply = _call_ollama(messages)
    except Exception as e:
        reply = f"Sorry, the local AI backend had an issue: {type(e).__name__}"

    # Save assistant turn and return
    add_turn(req.user_id, "assistant", reply)
    hist_msgs = [Message(role=r, content=c) for r, c in get_history(req.user_id)]
    return ChatResponse(reply=reply, history=hist_msgs, sources=sources)


from pathlib import Path
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parents[1]

@app.get("/")
def root():
    return RedirectResponse(url="/ui/")

app.mount("/ui", StaticFiles(directory=str(ROOT / "web"), html=True), name="web")



