"""Semantic caching layer using ChromaDB."""

import hashlib
from datetime import datetime, timedelta
from functools import lru_cache

import chromadb

from app.config import (
    CHROMA_DIR, 
    CACHE_COLLECTION_NAME, 
    CACHE_SIMILARITY_THRESHOLD, 
    CACHE_TTL_HOURS
)

@lru_cache(maxsize=1)
def get_cache_collection() -> chromadb.Collection:
    """Lazy-load the ChromaDB client and get/create the cache collection."""
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection(CACHE_COLLECTION_NAME)


def generate_cache_id(query: str) -> str:
    """Generate a deterministic ID based on the exact query text."""
    return hashlib.sha256(query.lower().strip().encode("utf-8")).hexdigest()


def check_cache(query: str) -> tuple[str | None, list[str]]:
    """
    Check if the query exists in the cache, satisfies the similarity threshold,
    and has not expired based on the TTL.
    
    Returns: A tuple of (cached_answer, sources) or (None, [])
    """
    try:
        collection = get_cache_collection()
        results = collection.query(query_texts=[query], n_results=1)

        if not results.get("documents") or not results["documents"][0]:
            return None, []

        distance = results["distances"][0][0]
        metadata = results["metadatas"][0][0]

        if distance > CACHE_SIMILARITY_THRESHOLD:
            return None, []

        cached_time = datetime.fromisoformat(metadata["timestamp"])
        if datetime.utcnow() - cached_time > timedelta(hours=CACHE_TTL_HOURS):
            return None, []

        # Return the valid cached answer and its original sources
        answer = results["documents"][0][0]
        sources = metadata.get("sources", "").split("|") if metadata.get("sources") else []
        return answer, sources

    except Exception as e:
        print(f"Cache Read Error: {e}")
        return None, []


def save_to_cache(query: str, answer: str, sources: list[str]) -> None:
    """Save a successful LLM response into the semantic cache."""
    try:
        collection = get_cache_collection()
        
        collection.add(
            documents=[answer],
            metadatas=[{
                "original_query": query,
                "timestamp": datetime.utcnow().isoformat(),
                "sources": "|".join(sources)
            }],
            ids=[generate_cache_id(query)] 
        )
    except Exception as e:
        print(f"Cache Write Error: {e}")