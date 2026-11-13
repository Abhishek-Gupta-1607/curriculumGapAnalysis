"""
backend/rag/chunking.py
========================
Splits document text into smaller chunks for embedding.

WHAT IS CHUNKING?
  Embedding models work best on focused text passages (100-500 words),
  not entire documents. Chunking breaks a long document into overlapping
  pieces so that:
  1. Each chunk is small enough to get a meaningful embedding.
  2. Overlapping ensures no information is lost at chunk boundaries.
  3. Each chunk keeps metadata (page number, section) for citations.

HOW IT WORKS:
  Document text → split into chunks of ~500 characters
  with ~50 character overlap between consecutive chunks.

  Example (chunk_size=20, overlap=5):
    "The quick brown fox jumps over the lazy dog"
    Chunk 1: "The quick brown fox " (chars 0-19)
    Chunk 2: " fox jumps over the " (chars 15-34)  ← overlaps by 5
    Chunk 3: " the lazy dog"       (chars 30-43)   ← overlaps by 5

WHY OVERLAP?
  Without overlap, a sentence split across two chunks might lose
  its meaning in both. Overlap ensures context is preserved.
"""

import re
import logging
from typing import Optional

from backend.config import settings

logger = logging.getLogger(__name__)


def chunk_document(
    document: dict,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
) -> list[dict]:
    """
    Split a loaded framework document into chunks with metadata.

    Args:
        document: Output from document_loader.load_framework_document().
        chunk_size: Max characters per chunk (default from settings).
        chunk_overlap: Overlap between chunks (default from settings).

    Returns:
        A list of chunk dictionaries:
        [
            {
                "chunk_id": "DOC-ID_chunk_001",
                "text": "chunk text...",
                "document_id": "DOC-ID",
                "document_name": "Framework Name",
                "page_number": 3,
                "section": "Detected section heading",
                "publisher": "NIST",
                "version": "Rev 1",
                "source_url": "https://...",
                "license": "Public Domain",
                "domain": "Data Science"
            },
            ...
        ]
    """
    if chunk_size is None:
        chunk_size = settings.RAG_CHUNK_SIZE
    if chunk_overlap is None:
        chunk_overlap = settings.RAG_CHUNK_OVERLAP

    chunks = []
    chunk_counter = 0
    current_framework_id = ""

    # Process each page separately to preserve page numbers
    for page in document.get("pages", []):
        page_text = page["text"]
        page_number = page["page_number"]
        sections = page.get("detected_sections", [])

        # Use the last detected section heading as context
        current_section = sections[-1] if sections else ""

        # Split this page's text into chunks
        page_chunks = _split_text(page_text, chunk_size, chunk_overlap)

        for chunk_text in page_chunks:
            if not chunk_text.strip():
                continue

            # Detect framework competency ID if present in chunk
            id_match = re.search(r"\[ID:\s*([A-Za-z0-9_\-]+)\]", chunk_text)
            if not id_match:
                id_match = re.search(r"Competency\s+([A-Za-z0-9_\-]+)", chunk_text)
            if id_match:
                current_framework_id = id_match.group(1).strip()

            chunk_counter += 1
            chunk_id = f"{document['document_id']}_chunk_{chunk_counter:03d}"

            chunks.append({
                "chunk_id": chunk_id,
                "text": chunk_text.strip(),
                "document_id": document["document_id"],
                "document_name": document["document_name"],
                "framework_id": current_framework_id,
                "page_number": page_number,
                "section": current_section,
                "publisher": document.get("publisher", ""),
                "version": document.get("version", ""),
                "source_url": document.get("source_url", ""),
                "license": document.get("license", ""),
                "domain": document.get("domain", ""),
            })

    logger.info(
        f"[Chunking] Created {len(chunks)} chunks from "
        f"'{document['document_name']}' "
        f"(chunk_size={chunk_size}, overlap={chunk_overlap})"
    )

    return chunks


def _split_text(
    text: str,
    chunk_size: int,
    chunk_overlap: int,
) -> list[str]:
    """
    Split text into overlapping chunks.

    Tries to split at sentence boundaries (periods followed by space)
    rather than cutting mid-word.

    Args:
        text: The text to split.
        chunk_size: Maximum characters per chunk.
        chunk_overlap: Number of overlapping characters.

    Returns:
        List of text chunks.
    """
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        # Take a chunk of chunk_size characters
        end = start + chunk_size

        if end >= len(text):
            # Last chunk — take everything remaining
            chunks.append(text[start:])
            break

        # Try to find a sentence boundary near the end
        # Look backwards from 'end' for a period+space or newline
        chunk_text = text[start:end]
        best_break = _find_best_break(chunk_text)

        if best_break > chunk_size // 2:
            # Found a good break point (not too early in the chunk)
            end = start + best_break
        # else: just cut at chunk_size (no good sentence boundary found)

        chunks.append(text[start:end].strip())

        # Move start forward, but overlap with previous chunk
        start = end - chunk_overlap

    return chunks


def _find_best_break(text: str) -> int:
    """
    Find the best position to break text (sentence/paragraph boundary).

    Priorities:
    1. Double newline (paragraph break)
    2. Single newline
    3. Period followed by space (sentence end)
    4. Space (word boundary)

    Returns the position of the best break, or len(text) if none found.
    """
    # Look for breaks in the last 30% of the text
    search_start = len(text) * 7 // 10

    # Try paragraph break first
    pos = text.rfind("\n\n", search_start)
    if pos > 0:
        return pos + 2  # After the double newline

    # Try single newline
    pos = text.rfind("\n", search_start)
    if pos > 0:
        return pos + 1

    # Try sentence end (. followed by space or newline)
    pos = text.rfind(". ", search_start)
    if pos > 0:
        return pos + 2

    # Try any space (word boundary)
    pos = text.rfind(" ", search_start)
    if pos > 0:
        return pos + 1

    # No good break found
    return len(text)
