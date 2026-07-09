"""Retrieve relevant chunks from ChromaDB."""

import sys
from dataclasses import dataclass
from functools import lru_cache

import chromadb

from app.config import CHROMA_DIR, COLLECTION_NAME, RAG_SEPARATOR


@dataclass
class RetrievedChunk:
    """A retrieved chunk with its source metadata."""
    text: str
    source: str
    section: str
    distance: float


@lru_cache(maxsize=1)
def get_db_client() -> chromadb.PersistentClient:
    """
    Lazy-load the ChromaDB client as a singleton.
    This prevents disk I/O side effects during module import and unit testing.
    """
    return chromadb.PersistentClient(path=str(CHROMA_DIR))


def retrieve(query: str, top_k: int = 3) -> list[RetrievedChunk]:
    """Return the top-k knowledge-base chunks most similar to the query."""
    client = get_db_client()
    collection = client.get_collection(COLLECTION_NAME)
    
    result = collection.query(query_texts=[query], n_results=top_k)

    if not result.get("documents") or not result["documents"][0]:
        return []

    return [
        RetrievedChunk(
            text=doc, 
            source=meta.get("source", "unknown"), 
            section=meta.get("section", "unknown"), 
            distance=dist
        )
        for doc, meta, dist in zip(
            result["documents"][0], result["metadatas"][0], result["distances"][0]
        )
    ]


def format_context(chunks: list[RetrievedChunk]) -> str:
    """Render chunks as a plain-text block for the LLM prompt."""
    return RAG_SEPARATOR.join(
        f"\n{c.text}" for c in chunks
    )


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")

    question = " ".join(sys.argv[1:]) or "How do I fix error E-101?"
    print(f"Query: {question!r}\n")
    
    for chunk in retrieve(question, top_k=3):
        print(f"--- {chunk.source} § {chunk.section}  (distance {chunk.distance:.3f})")
        print(chunk.text[:300].strip(), "...\n")