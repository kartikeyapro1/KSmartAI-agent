from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="GenAI Agent (Milestone 1)")

@app.get("/health")
def health():
    return {"status": "ok"}

class ChatRequest(BaseModel):
    user_id: str
    message: str

class ChatResponse(BaseModel):
    reply: str

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    # Echo for now; proves request/response flow works
    return ChatResponse(reply=f"You said: {req.message}")
