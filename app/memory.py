from collections import defaultdict, deque
from typing import Deque, Dict, List, Tuple

MAX_TURNS = 8  # keep last N messages per user

# user_id -> deque[(role, content)]
_store: Dict[str, Deque[Tuple[str, str]]] = defaultdict(lambda: deque(maxlen=MAX_TURNS))

def add_turn(user_id: str, role: str, content: str) -> None:
    _store[user_id].append((role, content))

def get_history(user_id: str) -> List[Tuple[str, str]]:
    return list(_store[user_id])

def clear(user_id: str) -> None:
    _store.pop(user_id, None)
