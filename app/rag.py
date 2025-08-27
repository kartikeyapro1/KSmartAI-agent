import os
import math
from pathlib import Path
import requests

DOCS_DIR = Path("data/docs")
DOCS_DIR.mkdir(parents=True, exist_ok=True)

EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
CI = os.getenv("CI") == "true" or os.getenv("EMBED_FAKE") == "true"

# Global in-memory index (lazy)
_EMB = []     # list[list[float]]
_TEXTS = []   # list[str]
_META = []    # list[str]

def _embed(text: str):
    """Return an embedding; on CI return a stub so we never call Ollama."""
    if CI:
        # 768 works for nomic-embed-text; zero vector avoids div-by-zero in cosine later
        return [0.0] * 768
    r = requests.post(
        f"{OLLAMA_URL}/api/embeddings",
        json={"model": EMBED_MODEL, "prompt": text},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["embedding"]

def build_index():
    texts, meta = [], []
    for p in DOCS_DIR.rglob("*"):
        if p.suffix.lower() in {".txt", ".md"}:
            try:
                txt = p.read_text(encoding="utf-8", errors="ignore").strip()
                if txt:
                    texts.append(txt)
                    meta.append(p.name)
            except Exception:
                # ignore unreadable files
                pass
    if not texts:
        return [], [], []
    vecs = [_embed(t) for t in texts]
    return vecs, texts, meta

def init_or_rebuild():
    """(Re)build the in-memory index. Safe on CI (no network)."""
    global _EMB, _TEXTS, _META
    try:
        _EMB, _TEXTS, _META = build_index()
        return {"chunks": len(_TEXTS)}
    except Exception as e:
        _EMB, _TEXTS, _META = [], [], []
        return {"chunks": 0, "error": type(e).__name__}

def search(query: str, k: int = 4):
    """Return up to k (snippet, source) pairs. If index is empty, return []."""
    if not _EMB or not _TEXTS:
        return []
    qv = _embed(query)

    def cosine(a, b):
        da = math.sqrt(sum(x * x for x in a))
        db = math.sqrt(sum(y * y for y in b))
        if da == 0.0 or db == 0.0:
            return 0.0
        return sum(x * y for x, y in zip(a, b)) / (da * db)

    sims = [(cosine(qv, v), i) for i, v in enumerate(_EMB)]
    sims.sort(reverse=True)
    out = []
    for _, i in sims[:k]:
        snippet = _TEXTS[i][:500]
        out.append((snippet, _META[i]))
    return out

# IMPORTANT: do NOT call init_or_rebuild() at import time.
# CI imports this module and would otherwise try to call Ollama.
