"""
backend/rag/ingestion.py
========================
Framework document ingestion pipeline.

WHAT THIS FILE DOES:
  1. Scans data/frameworks/ for industry framework PDFs.
  2. Extracts text and pages using document_loader (PyMuPDF).
  3. Splits text into semantic chunks with overlap using chunking.
  4. Generates dense embeddings using sentence-transformers (all-MiniLM-L6-v2).
  5. Stores chunks and vectors in persistent ChromaDB.
  6. Records metadata and status in SQLite database (FrameworkDocument table).

USAGE:
  from backend.rag.ingestion import ingest_all_frameworks
  results = ingest_all_frameworks()
"""

import os
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

from backend.config import settings
from backend.database.db import SessionLocal, init_database
from backend.database.models import FrameworkDocument
from backend.rag.document_loader import load_framework_document
from backend.rag.chunking import chunk_document
from backend.rag.embeddings import generate_embeddings
from backend.rag.vector_store import (
    add_chunks_to_store,
    get_collection_stats,
    clear_collection,
)

logger = logging.getLogger(__name__)

# Registry of known framework documents with verified public metadata
FRAMEWORK_CATALOG = [
    {
        "filename": "data_science_framework.pdf",
        "name": "Data Science Competency Framework",
        "publisher": "NIST NICE & European Commission ESCO",
        "version": "1.0",
        "source_url": "https://csrc.nist.gov/projects/nice-framework",
        "license": "Public Domain (NIST) / CC BY 4.0 (ESCO)",
        "domain": "Data Science",
    },
    {
        "filename": "web_development_framework.pdf",
        "name": "Web Development Competency Framework",
        "publisher": "European Commission ESCO & ACM CS2023",
        "version": "1.0",
        "source_url": "https://esco.ec.europa.eu/",
        "license": "CC BY 4.0 (ESCO) / Academic Use (ACM)",
        "domain": "Web Development",
    },
    {
        "filename": "cloud_devops_framework.pdf",
        "name": "Cloud and DevOps Competency Framework",
        "publisher": "NIST NICE & European Commission ESCO",
        "version": "1.0",
        "source_url": "https://csrc.nist.gov/publications/detail/sp/800-181/rev.1/final",
        "license": "Public Domain (NIST) / CC BY 4.0 (ESCO)",
        "domain": "Cloud and DevOps",
    },
]


def ingest_framework_file(
    pdf_path: str,
    name: str,
    publisher: str,
    version: str,
    source_url: str,
    license_info: str,
    domain: str,
    db_session = None,
) -> dict:
    """
    Ingest a single framework document into ChromaDB and SQLite.
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"Framework PDF not found: {pdf_path}")

    # 1. Load document with page structure
    doc_data = load_framework_document(
        pdf_path=str(path),
        document_name=name,
        publisher=publisher,
        version=version,
        source_url=source_url,
        license_info=license_info,
        domain=domain,
    )

    # 2. Chunk text
    chunks = chunk_document(doc_data)
    if not chunks:
        logger.warning(f"No chunks created for {name}")
        return {"name": name, "chunks": 0, "status": "EMPTY"}

    # 3. Generate embeddings
    texts = [c["text"] for c in chunks]
    embeddings = generate_embeddings(texts)

    # 4. Store in ChromaDB
    added = add_chunks_to_store(chunks, embeddings)

    # 5. Persist metadata in SQLite
    close_session = False
    if db_session is None:
        db_session = SessionLocal()
        close_session = True

    try:
        doc_record = (
            db_session.query(FrameworkDocument)
            .filter(FrameworkDocument.name == name)
            .first()
        )
        if not doc_record:
            doc_record = FrameworkDocument(
                id=doc_data["document_id"],
                name=name,
                publisher=publisher,
                version=version,
                source_url=source_url,
                license=license_info,
                domain=domain,
                download_date=datetime.utcnow(),
                chunk_count=added,
                ingestion_status="COMPLETED",
            )
            db_session.add(doc_record)
        else:
            doc_record.chunk_count = added
            doc_record.ingestion_status = "COMPLETED"
            doc_record.download_date = datetime.utcnow()

        db_session.commit()
    finally:
        if close_session:
            db_session.close()

    logger.info(f"Successfully ingested {name}: {added} chunks")
    return {
        "document_id": doc_data["document_id"],
        "name": name,
        "domain": domain,
        "pages": doc_data["total_pages"],
        "chunks": added,
        "status": "COMPLETED",
    }


def ingest_all_frameworks(reset_collection: bool = False) -> list[dict]:
    """
    Ingest all catalogued framework documents.
    """
    init_database()

    if reset_collection:
        clear_collection()

    results = []
    frameworks_dir = Path(settings.FRAMEWORKS_DIR)
    db = SessionLocal()

    try:
        for entry in FRAMEWORK_CATALOG:
            pdf_path = frameworks_dir / entry["filename"]
            if not pdf_path.exists():
                logger.warning(f"File not found, skipping: {pdf_path}")
                continue

            res = ingest_framework_file(
                pdf_path=str(pdf_path),
                name=entry["name"],
                publisher=entry["publisher"],
                version=entry["version"],
                source_url=entry["source_url"],
                license_info=entry["license"],
                domain=entry["domain"],
                db_session=db,
            )
            results.append(res)
    finally:
        db.close()

    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Starting framework document ingestion...")
    results = ingest_all_frameworks()
    print("Ingestion results:")
    for r in results:
        print(f"  - {r['domain']}: {r['name']} ({r['chunks']} chunks, {r['status']})")
    stats = get_collection_stats()
    print(f"ChromaDB total documents: {stats['total_documents']}")
