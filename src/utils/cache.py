
from typing import Dict, Tuple, Optional, List
import hashlib
from datetime import datetime, timedelta

class VerificationCache:
    """
    Simple in-memory cache for LLM verification results.
    Stores results keyed by (query + url) hash.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VerificationCache, cls).__new__(cls)
            cls._instance._cache = {}
            cls._instance._ttl = timedelta(hours=24) # Cache for 24 hours
        return cls._instance
    
    def _generate_key(self, query: str, url: str) -> str:
        """Generates a stable cache key."""
        content = f"{query.strip().lower()}|{url.strip()}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, query: str, url: str) -> Optional[Tuple[bool, float]]:
        """Retrieves cached result if exists and not expired."""
        key = self._generate_key(query, url)
        entry = self._cache.get(key)
        
        if not entry:
            return None
            
        timestamp, result = entry
        if datetime.now() - timestamp > self._ttl:
            del self._cache[key]
            return None
            
        return result
    
    def set(self, query: str, url: str, result: Tuple[bool, float]) -> None:
        """Stores result in cache."""
        key = self._generate_key(query, url)
        self._cache[key] = (datetime.now(), result)
        
    def clear(self) -> None:
        """Clears the entire cache."""
        self._cache.clear()

class QueryCache:
    """
    Simple in-memory cache for search query generation.
    Stores results keyed by (original_query + context) hash.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(QueryCache, cls).__new__(cls)
            cls._instance._cache = {}
            cls._instance._ttl = timedelta(hours=1) # Cache for 1 hour
        return cls._instance
    
    def _generate_key(self, query: str, context: Optional[str]) -> str:
        """Generates a stable cache key."""
        ctx = context.strip().lower() if context else ""
        content = f"{query.strip().lower()}|{ctx}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, query: str, context: Optional[str]) -> Optional[List[str]]:
        """Retrieves cached queries if exists and not expired."""
        key = self._generate_key(query, context)
        entry = self._cache.get(key)
        
        if not entry:
            return None
            
        timestamp, result = entry
        if datetime.now() - timestamp > self._ttl:
            del self._cache[key]
            return None
            
        return result
    
    def set(self, query: str, context: Optional[str], result: List[str]) -> None:
        """Stores queries in cache."""
        key = self._generate_key(query, context)
        self._cache[key] = (datetime.now(), result)
    
    def clear(self) -> None:
        """Clears the entire cache."""
        self._cache.clear()
