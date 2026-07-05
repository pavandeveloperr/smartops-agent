"""Chunk and ingest the knowledge base into ChromaDB."""

from pathlib import Path

import chromadb
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE_BASE_DIR = REPO_ROOT / "knowledge_base"
CHROMA_DIR = str(REPO_ROOT / ".chroma")
COLLECTION_NAME = "smartops_kb"

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150


def build_chunks() -> tuple[list[str], list[dict], list[str]]:
    """Read every markdown file and return documents, metadata, and ids for Chroma."""
    header_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[("#", "title"), ("##", "section")],
    )
    size_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
    )

    documents: list[str] = []
    metadatas: list[dict] = []
    ids: list[str] = []

    for md_file in sorted(KNOWLEDGE_BASE_DIR.glob("*.md")):
        text = md_file.read_text(encoding="utf-8")
        for i, section in enumerate(size_splitter.split_documents(header_splitter.split_text(text))):
            title = section.metadata.get("title", "")
            heading = section.metadata.get("section", "")
            documents.append(f"{title} — {heading}\n\n{section.page_content}")
            metadatas.append({"source": md_file.name, "section": heading or title})
            ids.append(f"{md_file.stem}-{i}")

    return documents, metadatas, ids


def ingest() -> None:
    """Rebuild the Chroma collection from scratch."""
    documents, metadatas, ids = build_chunks()

    client = chromadb.PersistentClient(path=CHROMA_DIR)

    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(COLLECTION_NAME)

    collection.add(documents=documents, metadatas=metadatas, ids=ids)

    print(f"Ingested {collection.count()} chunks from "
          f"{len(set(m['source'] for m in metadatas))} files into '{COLLECTION_NAME}' at {CHROMA_DIR}")


if __name__ == "__main__":
    ingest()
