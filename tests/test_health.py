from fastapi.testclient import TestClient
import app.main as main

def test_health_ok(monkeypatch):
    # Force the "ollama" branch of /health
    monkeypatch.setattr(main, "PROVIDER", "ollama", raising=False)

    class _Resp:
        def raise_for_status(self):  # simulate 200 OK from /api/tags
            return None

    def fake_get(url, timeout):
        assert "http://localhost:11434/api/tags" in url
        return _Resp()

    # Patch only main.requests.get, not the global requests module
    monkeypatch.setattr(main.requests, "get", fake_get, raising=True)

    client = TestClient(main.app)
    r = client.get("/health")
    assert r.status_code == 200
    j = r.json()
    assert j["status"] == "ok"
    assert j["provider"] == "ollama"
    assert "model" in j
