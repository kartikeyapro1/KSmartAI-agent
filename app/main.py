import os
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.schemas import ChatRequest, ChatResponse, Message
from app.memory import add_turn, get_history, clear

# ----- config -----
load_dotenv()  # loads .env at project root

PROVIDER = os.getenv("PROVIDER", "ollama").lower()
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")
SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT", "You are a helpful assistant.")

app = FastAPI(title="GenAI Agent (Milestone 3A — Ollama)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

@app.get("/health")
def health():
    # try to ping ollama
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

def _build_messages(user_id: str, user_msg: str):
    # System prompt + last turns + current user message
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for role, content in get_history(user_id):
        if role in ("user", "assistant"):
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": user_msg})

    # guardrail: cap total chars
    MAX_CHARS = 12000
    total = 0
    trimmed = []
    for m in reversed(messages):
        c = len(m["content"])
        if total + c <= MAX_CHARS or m["role"] == "system":
            trimmed.append(m)
            total += c
    return list(reversed(trimmed))

def _call_ollama(messages):
    # Ollama chat API accepts "messages" with role/content just like OpenAI
    r = requests.post(
        "http://localhost:11434/api/chat",
        json={"model": OLLAMA_MODEL, "messages": messages, "stream": False},
        timeout=300,
    )
    r.raise_for_status()
    data = r.json()
    # Response shape: {"message": {"role": "assistant", "content": "..."} , ...}
    return data["message"]["content"].strip()

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    # store user message
    add_turn(req.user_id, "user", req.message)

    messages = _build_messages(req.user_id, req.message)
    try:
        reply = _call_ollama(messages)
    except Exception as e:
        reply = f"Sorry, the local AI backend had an issue: {type(e).__name__}"

    # store assistant reply
    add_turn(req.user_id, "assistant", reply)

    # return updated history
    hist_msgs = [Message(role=r, content=c) for r, c in get_history(req.user_id)]
    return ChatResponse(reply=reply, history=hist_msgs)

@app.post("/memory/{user_id}/clear")
def clear_memory(user_id: str):
    clear(user_id)
    return {"ok": True, "message": f"memory cleared for {user_id}"}
