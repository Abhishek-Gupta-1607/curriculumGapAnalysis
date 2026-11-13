"""
backend/rag/vector_store.py
============================
ChromaDB vector store operations.

WHAT IS ChromaDB?
  ChromaDB is a vector database that stores embeddings (number lists)
  and retrieves the most similar ones efficiently. Think of it as a
  "search engine for meaning" — instead of matching exact keywords,
  it finds texts with the most similar meaning.

WHY ChromaDB?
  - Runs locally (no server needed, unlike Pinecone or Weaviate).
  - Persistent storage (data survives restarts).
  - Simple Python API.
  - Handles both storage and retrieval.
  - Free and open source.

HOW IT WORKS IN OUR PROJECT:
  1. INGESTION: Framework document chunks → embeddings → stored in ChromaDB.
  2. RETRIEVAL: Syllabus topic → embedding → ChromaDB finds similar chunks.
  3. The retrieved chunks become "evidence" for gap analysis.
"""

import logging
from typing import Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from backend.config import settings

logger = logging.getLogger(__name__)

# ── Module-level client cache ──
_client = None


def get_chroma_client() -> chromadb.ClientAPI:
    """
    Get or create the ChromaDB persistent client.

    The client connects to a local database stored in storage/chroma_db/.
    Data persists between application restarts.
    """
    global _client

    if _client is None:
        _client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        logger.info(
            f"[VectorStore] ChromaDB client initialised at "
            f"{settings.CHROMA_PERSIST_DIR}"
        )

    return _client


def get_or_create_collection(
    collection_name: str = "framework_skills",
) -> chromadb.Collection:
    """
    Get or create a ChromaDB collection.

    A collection is like a table — it groups related embeddings.
    We use one collection for all framework skill chunks.

    Args:
        collection_name: Name of the collection.

    Returns:
        The ChromaDB collection object.
    """
    client = get_chroma_client()
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"description": "Industry framework skill chunks"},
    )

    logger.info(
        f"[VectorStore] Collection '{collection_name}': "
        f"{collection.count()} documents"
    )
    return collection


def add_chunks_to_store(
    chunks: list[dict],
    embeddings: list[list[float]],
    collection_name: str = "framework_skills",
) -> int:
    """
    Add document chunks and their embeddings to ChromaDB.

    Args:
        chunks: List of chunk dictionaries from chunking.chunk_document().
        embeddings: Matching embedding vectors from embeddings.generate_embeddings().
        collection_name: Name of the target collection.

    Returns:
        Number of chunks added.

    Each chunk is stored with:
      - ID: chunk_id (unique identifier)
      - Embedding: the vector representation
      - Document: the actual text
      - Metadata: page number, section, source info (for citations)
    """
    if not chunks or not embeddings:
        logger.warning("[VectorStore] No chunks or embeddings to add")
        return 0

    if len(chunks) != len(embeddings):
        raise ValueError(
            f"Mismatch: {len(chunks)} chunks but {len(embeddings)} embeddings"
        )

    collection = get_or_create_collection(collection_name)

    # Prepare data for ChromaDB
    ids = []
    documents = []
    metadatas = []

    for chunk in chunks:
        ids.append(chunk["chunk_id"])
        documents.append(chunk["text"])
        metadatas.append({
            "document_id": chunk.get("document_id", ""),
            "document_name": chunk.get("document_name", ""),
            "framework_id": chunk.get("framework_id", ""),
            "page_number": chunk.get("page_number", 0),
            "section": chunk.get("section", ""),
            "publisher": chunk.get("publisher", ""),
            "version": chunk.get("version", ""),
            "source_url": chunk.get("source_url", ""),
            "license": chunk.get("license", ""),
            "domain": chunk.get("domain", ""),
        })

    # Add to ChromaDB in batches (ChromaDB has a batch size limit)
    batch_size = 100
    total_added = 0

    for i in range(0, len(ids), batch_size):
        batch_end = min(i + batch_size, len(ids))
        collection.add(
            ids=ids[i:batch_end],
            embeddings=embeddings[i:batch_end],
            documents=documents[i:batch_end],
            metadatas=metadatas[i:batch_end],
        )
        total_added += batch_end - i

    logger.info(
        f"[VectorStore] Added {total_added} chunks to '{collection_name}' "
        f"(total: {collection.count()})"
    )

    return total_added


def search_similar(
    query_embedding: list[float],
    top_k: Optional[int] = None,
    domain_filter: Optional[str] = None,
    collection_name: str = "framework_skills",
) -> list[dict]:
    """
    Search for the most similar chunks to a query embedding.

    Args:
        query_embedding: The vector to search for.
        top_k: Number of results to return (default from settings).
        domain_filter: Optional domain to filter results (e.g. "Data Science").
        collection_name: Which collection to search.

    Returns:
        List of result dictionaries, ordered by similarity (best first):
        [
            {
                "chunk_id": "DOC-ID_chunk_003",
                "text": "Retrieved passage...",
                "similarity_score": 0.87,
                "metadata": {
                    "document_name": "...",
                    "page_number": 5,
                    "section": "...",
                    ...
                }
            },
            ...
        ]
    """
    if top_k is None:
        top_k = settings.RAG_TOP_K

    collection = get_or_create_collection(collection_name)

    if collection.count() == 0:
        logger.warning("[VectorStore] Collection is empty — no results")
        return []

    # Build query parameters
    query_params = {
        "query_embeddings": [query_embedding],
        "n_results": min(top_k, collection.count()),
        "include": ["documents", "metadatas", "distances"],
    }

    # Add domain filter if specified
    if domain_filter:
        query_params["where"] = {"domain": domain_filter}

    results = collection.query(**query_params)

    # Convert ChromaDB results to our format
    # ChromaDB returns distances (lower = more similar)
    # We convert to similarity scores (higher = more similar)
    formatted_results = []

    if results and results["ids"] and results["ids"][0]:
        for i, chunk_id in enumerate(results["ids"][0]):
            # ChromaDB uses L2 distance by default
            # Convert distance to a similarity-like score (0-1 range)
            distance = results["distances"][0][i] if results["distances"] else 0
            # For L2 distance: similarity ≈ 1 / (1 + distance)
            similarity = 1.0 / (1.0 + distance)

            formatted_results.append({
                "chunk_id": chunk_id,
                "text": results["documents"][0][i] if results["documents"] else "",
                "similarity_score": round(similarity, 4),
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
            })

    logger.info(
        f"[VectorStore] Search returned {len(formatted_results)} results"
    )

    return formatted_results


def get_collection_stats(
    collection_name: str = "framework_skills",
) -> dict:
    """
    Get statistics about a collection.

    Returns:
        {
            "collection_name": "framework_skills",
            "total_documents": 150,
            "domains": ["Data Science", "Web Development", ...],
        }
    """
    collection = get_or_create_collection(collection_name)
    count = collection.count()

    # Try to get unique domains from metadata
    domains = set()
    if count > 0:
        # Sample some entries to find domains
        sample = collection.peek(limit=min(count, 100))
        if sample and sample.get("metadatas"):
            for meta in sample["metadatas"]:
                if meta and meta.get("domain"):
                    domains.add(meta["domain"])

    return {
        "collection_name": collection_name,
        "total_documents": count,
        "domains": sorted(list(domains)),
    }


def clear_collection(collection_name: str = "framework_skills") -> None:
    """
    Delete all documents from a collection.
    Useful for re-ingestion or testing.
    """
    client = get_chroma_client()
    try:
        client.delete_collection(collection_name)
        logger.info(f"[VectorStore] Deleted collection '{collection_name}'")
    except Exception:
        logger.info(f"[VectorStore] Collection '{collection_name}' does not exist")
