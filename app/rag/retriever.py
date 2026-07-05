"""Retrieve relevant chunks from ChromaDB."""

import sys
from dataclasses import dataclass

import chromadb

from app.rag.ingest import CHROMA_DIR, COLLECTION_NAME


@dataclass
class RetrievedChunk:
    """A retrieved chunk with its source metadata."""
    text: str
    source: str
    section: str
    distance: float


_client = chromadb.PersistentClient(path=CHROMA_DIR)


def retrieve(query: str, top_k: int = 3) -> list[RetrievedChunk]:
    """Return the top-k knowledge-base chunks most similar to the query."""
    collection = _client.get_collection(COLLECTION_NAME)
    result = collection.query(query_texts=[query], n_results=top_k)

    return [
        RetrievedChunk(text=doc, source=meta["source"], section=meta["section"], distance=dist)
        for doc, meta, dist in zip(
            result["documents"][0], result["metadatas"][0], result["distances"][0]
        )
    ]


def format_context(chunks: list[RetrievedChunk]) -> str:
    """Render chunks as a plain-text block for the LLM prompt."""
    return "\n\n---\n\n".join(
        f"[source: {c.source} § {c.section}]\n{c.text}" for c in chunks
    )


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")

    question = " ".join(sys.argv[1:]) or "How do I fix error E-101?"
    print(f"Query: {question!r}\n")
    for chunk in retrieve(question, top_k=3):
        print(f"--- {chunk.source} § {chunk.section}  (distance {chunk.distance:.3f})")
        print(chunk.text[:300].strip(), "...\n")
