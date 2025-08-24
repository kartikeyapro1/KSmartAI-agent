from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import ChatRequest, ChatResponse, Message
from app.memory import add_turn, get_history, clear

app = FastAPI(title="GenAI Agent (Milestone 2)")

# CORS so a frontend can call this later from http://localhost
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later if you want
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """
    Simple 'assistant' that demonstrates memory.
    It echoes your message, and—if there was a prior user message—references it.
    """
    history = get_history(req.user_id)
    last_user_before = None
    for role, content in reversed(history):
        if role == "user":
            last_user_before = content
            break

    # store this user turn
    add_turn(req.user_id, "user", req.message)

    if last_user_before:
        reply = f"You said: {req.message}\n(Previously you mentioned: '{last_user_before}')"
    else:
        reply = f"You said: {req.message}"

    # store assistant reply
    add_turn(req.user_id, "assistant", reply)

    # build history payload
    hist_msgs = [Message(role=r, content=c) for r, c in get_history(req.user_id)]
    return ChatResponse(reply=reply, history=hist_msgs)

@app.post("/memory/{user_id}/clear")
def clear_memory(user_id: str):
    clear(user_id)
    return {"ok": True, "message": f"memory cleared for {user_id}"}
