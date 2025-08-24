import re

# minimal patterns; this is illustrative, not exhaustive
_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE = re.compile(r"\+?\d[\d\-\s]{7,}\d")
_BAD_WORDS = {"fuck", "shit"}  # tiny demo list

def sanitize(text: str) -> str:
    red = _EMAIL.sub("[EMAIL]", text)
    red = _PHONE.sub("[PHONE]", red)
    return red

def flags(text: str):
    f = []
    if _EMAIL.search(text): f.append("email")
    if _PHONE.search(text): f.append("phone")
    if any(w in text.lower() for w in _BAD_WORDS): f.append("profanity")
    return f
