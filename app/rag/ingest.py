import chromadb
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

from app.config import (
    KNOWLEDGE_BASE_DIR,
    CHROMA_DIR,
    COLLECTION_NAME,
    CHUNK_SIZE,
    CHUNK_OVERLAP
)


def build_chunks() -> tuple[list[str], list[dict], list[str]]:
    """Read every markdown file and return documents, metadata, and ids for Chroma."""
    
    if not KNOWLEDGE_BASE_DIR.exists():
        print(f"Warning: Knowledge base directory not found at {KNOWLEDGE_BASE_DIR}")
        return [], [], []

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
    
    if not documents:
        print("No documents found to ingest. Exiting.")
        return

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    try:
        client.delete_collection(COLLECTION_NAME)
    except ValueError:
        pass
        
    collection = client.create_collection(COLLECTION_NAME)
    collection.add(documents=documents, metadatas=metadatas, ids=ids)

    print(
        f"Ingested {collection.count()} chunks from "
        f"{len(set(m['source'] for m in metadatas))} files into '{COLLECTION_NAME}'"
    )


if __name__ == "__main__":
    ingest()