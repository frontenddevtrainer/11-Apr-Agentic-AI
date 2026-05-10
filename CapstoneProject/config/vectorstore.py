"""
ChromaDB setup with multiple collections:
  - feedback_embeddings:  Raw reviews & emails for duplicate detection
  - ticket_embeddings:    Generated tickets for duplicate detection
  - product_docs:         Technical product documentation for Bug/Feature agents
"""

from pathlib import Path

import chromadb

from config.settings import (
    CHROMA_PERSIST_DIR,
    CHROMA_COLLECTION_FEEDBACK,
    CHROMA_COLLECTION_TICKETS,
    CHROMA_COLLECTION_PRODUCT_DOCS,
    PRODUCT_DOCS_DIR,
)


def get_chroma_client():
    """Return a persistent ChromaDB client."""
    CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(CHROMA_PERSIST_DIR))


# ── Collection getters ──────────────────────────────────────────────

def get_feedback_collection():
    """Collection for raw user feedback (reviews + emails)."""
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=CHROMA_COLLECTION_FEEDBACK,
        metadata={"description": "Raw user feedback for duplicate detection"},
    )


def get_ticket_collection():
    """Collection for generated tickets (for duplicate detection)."""
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=CHROMA_COLLECTION_TICKETS,
        metadata={"description": "Generated tickets for duplicate detection"},
    )


def get_product_docs_collection():
    """Collection for product technical documentation."""
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=CHROMA_COLLECTION_PRODUCT_DOCS,
        metadata={"description": "Product docs for Bug/Feature agent context"},
    )


# ── Generic helpers ─────────────────────────────────────────────────

def upsert_documents(collection, ids: list[str], documents: list[str], metadatas: list[dict]):
    """Upsert documents into any ChromaDB collection."""
    collection.upsert(ids=ids, documents=documents, metadatas=metadatas)


def query_similar(collection, query_text: str, n_results: int = 5):
    """Query a collection for similar documents."""
    count = collection.count()
    if count == 0:
        return {"ids": [[]], "documents": [[]], "distances": [[]], "metadatas": [[]]}
    actual_n = min(n_results, count)
    return collection.query(query_texts=[query_text], n_results=actual_n)


# ── Product docs loader ─────────────────────────────────────────────

def load_product_docs():
    """
    Read all .md files from PRODUCT_DOCS_DIR and upsert them
    into the product_docs ChromaDB collection (chunked by section).
    """
    collection = get_product_docs_collection()
    docs_dir = Path(PRODUCT_DOCS_DIR)
    if not docs_dir.exists():
        return 0

    ids, documents, metadatas = [], [], []
    chunk_id = 0

    for md_file in sorted(docs_dir.glob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        filename = md_file.name

        # Split by ## headings into chunks for better retrieval
        sections = _split_into_sections(content)
        for section_title, section_body in sections:
            if len(section_body.strip()) < 20:
                continue
            chunk_id += 1
            ids.append(f"doc_{filename}_{chunk_id}")
            documents.append(f"{section_title}\n{section_body}")
            metadatas.append({"source": filename, "section": section_title})

    if ids:
        upsert_documents(collection, ids, documents, metadatas)
    return len(ids)


def _split_into_sections(markdown_text: str) -> list[tuple[str, str]]:
    """Split markdown into (heading, body) tuples by ## headings."""
    sections = []
    current_heading = "Introduction"
    current_body_lines = []

    for line in markdown_text.split("\n"):
        if line.startswith("## "):
            if current_body_lines:
                sections.append((current_heading, "\n".join(current_body_lines)))
            current_heading = line.lstrip("#").strip()
            current_body_lines = []
        elif line.startswith("# ") and not current_body_lines:
            current_heading = line.lstrip("#").strip()
        else:
            current_body_lines.append(line)

    if current_body_lines:
        sections.append((current_heading, "\n".join(current_body_lines)))

    return sections
