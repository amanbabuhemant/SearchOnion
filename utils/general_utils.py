from hashlib import sha256
from functools import lru_cache


@lru_cache
def hash_sha256(s: str) -> str:
    """
    Return hash of string `s`
    """
    return sha256(s.encode()).hexdigest()
