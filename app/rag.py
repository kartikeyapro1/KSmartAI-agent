import os, glob
import numpy as np
import requests
from typing import List, Tuple
from pypdf import PdfReader

EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
DOCS_PATH = "data/docs"

# In-memory index
_EMB = np.zeros((0, 0), dtype=np.float32)
_TEXTS: List[str] = []
_META: List[str] = []

def _read_file(path: str) -> str:
    p = path.lower()
    if p.endswith(".pdf"):
        reader = PdfReader(path)
        return "\n".join([(pg.extract_text() or "") for pg in reader.pages])
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def _chunk(text: str, size: int = 800, overlap: int = 120) -> List[str]:
    chunks, i = [], 0
    step = max(1, size - overlap)
    while i < len(text):
        part = text[i:i+size].strip()
        if part:
            chunks.append(part)
        i += step
    return chunks

def _embed(text: str) -> np.ndarray:
    r = requests.post(
        "http://localhost:11434/api/embeddings",
        json={"model": EMBED_MODEL, "prompt": text},
        timeout=180
    )
    r.raise_for_status()
    vec = np.array(r.json()["embedding"], dtype=np.float32)
    return vec

def build_index() -> tuple[np.ndarray, List[str], List[str]]:
    texts, meta = [], []
    for path in glob.glob(f"{DOCS_PATH}/**/*", recursive=True):
        if os.path.isdir(path):
            continue
        if not path.lower().endswith((".txt", ".md", ".pdf")):
            continue
        try:
            raw = _read_file(path)
            for ch in _chunk(raw):
                texts.append(ch)
                meta.append(os.path.basename(path))
        except Exception:
            continue

    if not texts:
        return np.zeros((0, 0), dtype=np.float32), [], []

    vecs = [_embed(t) for t in texts]
    M = np.vstack(vecs).astype(np.float32)
    # L2-normalize so dot product == cosine similarity
    norms = np.linalg.norm(M, axis=1, keepdims=True) + 1e-12
    M = M / norms
    return M, texts, meta

def init_or_rebuild() -> dict:
    global _EMB, _TEXTS, _META
    _EMB, _TEXTS, _META = build_index()
    return {"chunks": len(_TEXTS), "dims": (int(_EMB.shape[1]) if _EMB.size else 0)}

# Build once on import
init_or_rebuild()

def search(query: str, k: int = 4) -> List[Tuple[str, str]]:
    if _EMB.size == 0:
        return []
    q = _embed(query).astype(np.float32)
    q = q / (np.linalg.norm(q) + 1e-12)
    scores = _EMB @ q  # cosine similarity
    idx = np.argsort(-scores)[:k]
    return [(_TEXTS[i], _META[i]) for i in idx]
