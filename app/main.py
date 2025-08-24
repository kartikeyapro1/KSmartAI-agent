import os
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.schemas import ChatRequest, ChatResponse, Message
from app.memory import add_turn, get_history, clear
from app import rag

load_dotenv()

PROVIDER = os.getenv("PROVIDER", "ollama").lower()
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")
SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT", "You are a helpful assistant.")

app = FastAPI(title="GenAI Agent (Milestone 4 — RAG + Ollama)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

@app.get("/health")
def health():
    ok = True
    if PROVIDER == "ollama":
        try:
            r = requests.get("http://localhost:11434/api/tags", timeout=2)
            r.raise_for_status()
        except Exception:
            ok = False
    return {
        "status": "ok" if ok else "ollama-unreachable",
        "provider": PROVIDER,
        "model": OLLAMA_MODEL,
    }

@app.post("/memory/{user_id}/clear")
def clear_memory(user_id: str):
    clear(user_id)
    return {"ok": True, "message": f"memory cleared for {user_id}"}

@app.post("/reindex")
def reindex():
    info = rag.init_or_rebuild()
    return {"ok": True, "index": info}

def _call_ollama(messages):
    r = requests.post(
        "http://localhost:11434/api/chat",
        json={"model": OLLAMA_MODEL, "messages": messages, "stream": False},
        timeout=600,
    )
    r.raise_for_status()
    data = r.json()
    return data["message"]["content"].strip()

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    # Save user turn
    add_turn(req.user_id, "user", req.message)

    # RAG search
    hits = rag.search(req.message, k=4)
    context_blocks = [f"[{src}] {txt}" for (txt, src) in hits]
    sources = list(dict.fromkeys([src for (_, src) in hits])) or None

    # Build messages (system + CONTEXT + memory + current user)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": (
            "You have access to a CONTEXT block with snippets from the user's documents.\n"
            "If the answer is in CONTEXT, use it and cite the file names.\n"
            "If the answer isn't in CONTEXT, say you don't know.\n"
            "Be concise."
        )},
    ]
    if context_blocks:
        messages.append({"role": "system", "content": "CONTEXT:\n" + "\n\n".join(context_blocks)})

    for role, content in get_history(req.user_id):
        if role in ("user", "assistant"):
            messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": req.message})

    # Guardrail: trim to ~12k chars (keep newest)
    MAX_CHARS = 12000
    total, trimmed = 0, []
    for m in reversed(messages):
        c = len(m["content"])
        if total + c <= MAX_CHARS or m["role"] == "system":
            trimmed.append(m)
            total += c
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
