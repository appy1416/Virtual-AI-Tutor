import logging
from typing import Set

logger = logging.getLogger("edutwin.cache")

class TokenBlacklist:
    """
    Manages active token revocation.
    Uses a simple thread-safe in-memory cache for the MVP.
    """
    def __init__(self):
        self._memory_blacklist: Set[str] = set()
        logger.info("Initialized in-memory token blacklist.")

    def blacklist_token(self, token: str, expire_seconds: int = 86400) -> None:
        self._memory_blacklist.add(token)

    def is_token_blacklisted(self, token: str) -> bool:
        return token in self._memory_blacklist

# Global instance
token_blacklist = TokenBlacklist()

