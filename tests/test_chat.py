from fastapi.testclient import TestClient
import app.main as main
from app import rag

def test_chat_with_monkeypatched_llm_and_rag(monkeypatch):
    client = TestClient(main.app)

    # 1) Patch RAG search to return a deterministic snippet and source
    def fake_search(query: str, k: int = 4):
        return [("Kartikeya Sharma is a Computer Systems Engineering student.", "about-kart.txt")]
    monkeypatch.setattr(rag, "search", fake_search, raising=True)

    # 2) Patch Ollama call to avoid hitting the local server
    def fake_call_ollama(messages):
        # make sure context was injected
        joined = "\n".join(m["content"] for m in messages if m["role"] in ("system", "user", "assistant"))
        assert "CONTEXT:" in joined
        # return a deterministic model reply
        return "Stubbed LLM reply."
    monkeypatch.setattr(main, "_call_ollama", fake_call_ollama, raising=True)

    # 3) Call /chat and assert response shape and sources
    payload = {"user_id": "kart", "message": "What degree does Kartikeya study?"}
    r = client.post("/chat", json=payload)
    assert r.status_code == 200
    j = r.json()
    assert j["reply"] == "Stubbed LLM reply."
    assert isinstance(j["history"], list) and len(j["history"]) >= 2
    assert "sources" in j and j["sources"] == ["about-kart.txt"]

def test_reindex_endpoint(monkeypatch):
    client = TestClient(main.app)

    # Patch rag.init_or_rebuild so we don't compute embeddings during the test
    def fake_reindex():
        return {"chunks": 1, "dims": 768}
    monkeypatch.setattr(rag, "init_or_rebuild", fake_reindex, raising=True)

    r = client.post("/reindex")
    assert r.status_code == 200
    j = r.json()
    assert j["ok"] is True
    assert j["index"] == {"chunks": 1, "dims": 768}
