"""
backend/rag/document_loader.py
===============================
Loads industry framework PDF documents and extracts text with metadata.

WHAT THIS FILE DOES:
  - Opens a framework PDF using PyMuPDF.
  - Extracts text page by page.
  - Tries to detect section headings from the text structure.
  - Returns a list of page records with text and metadata.

WHY SEPARATE FROM pdf_service.py?
  pdf_service.py handles general PDF extraction (for syllabi too).
  document_loader.py adds framework-specific metadata extraction:
    - Section heading detection.
    - Framework document metadata (publisher, version, URL).
    - Prepares data specifically for the chunking step.
"""

import re
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def load_framework_document(
    pdf_path: str,
    document_name: str,
    publisher: str = "",
    version: str = "",
    source_url: str = "",
    license_info: str = "",
    domain: str = "",
) -> dict:
    """
    Load a framework PDF and extract text with page-level metadata.

    Args:
        pdf_path: Path to the framework PDF file.
        document_name: Human-readable name of the document.
        publisher: Who published it (e.g. "NIST", "European Commission").
        version: Document version string.
        source_url: Where to find the original document.
        license_info: License type (e.g. "Public Domain", "CC BY 4.0").
        domain: Primary domain (e.g. "Data Science", "Cybersecurity").

    Returns:
        {
            "document_id": "generated-from-name",
            "document_name": "...",
            "publisher": "...",
            "version": "...",
            "source_url": "...",
            "license": "...",
            "domain": "...",
            "total_pages": N,
            "pages": [
                {
                    "page_number": 1,
                    "text": "...",
                    "detected_sections": ["Section A", "Section B"]
                },
                ...
            ],
            "full_text": "All text combined...",
            "errors": []
        }
    """
    import pymupdf as fitz

    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"Framework document not found: {pdf_path}")

    # Generate a simple document ID from the name
    doc_id = re.sub(r"[^a-zA-Z0-9]", "-", document_name).strip("-").upper()[:30]

    result = {
        "document_id": doc_id,
        "document_name": document_name,
        "publisher": publisher,
        "version": version,
        "source_url": source_url,
        "license": license_info,
        "domain": domain,
        "total_pages": 0,
        "pages": [],
        "full_text": "",
        "errors": [],
    }

    try:
        doc = fitz.open(str(path))
        result["total_pages"] = len(doc)
        all_text_parts = []

        for page_num in range(len(doc)):
            try:
                page = doc.load_page(page_num)
                page_text = page.get_text()

                if page_text.strip():
                    # Try to detect section headings
                    # Headings are often lines that are:
                    #   - Short (< 100 chars)
                    #   - Followed by a blank line or longer text
                    #   - Sometimes ALL CAPS or Title Case
                    sections = _detect_sections(page_text)

                    all_text_parts.append(page_text)
                    result["pages"].append({
                        "page_number": page_num + 1,
                        "text": page_text.strip(),
                        "detected_sections": sections,
                    })
                else:
                    result["errors"].append(
                        f"Page {page_num + 1}: No extractable text"
                    )
            except Exception as e:
                result["errors"].append(
                    f"Page {page_num + 1}: {str(e)}"
                )

        result["full_text"] = "\n\n".join(all_text_parts)
        doc.close()

        logger.info(
            f"[DocLoader] Loaded '{document_name}': "
            f"{len(result['pages'])} pages, "
            f"{len(result['full_text'])} chars"
        )

    except Exception as e:
        raise ValueError(f"Error loading framework document: {str(e)}")

    return result


def _detect_sections(page_text: str) -> list[str]:
    """
    Simple heuristic to find section headings in page text.

    Looks for lines that:
    1. Are relatively short (< 80 chars).
    2. Start with a number or capital letter.
    3. Don't end with common sentence-ending punctuation.

    This is a best-effort heuristic — not perfect for all documents.
    """
    sections = []
    lines = page_text.strip().split("\n")

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Skip very short lines (page numbers, etc.) and very long lines
        if len(stripped) < 5 or len(stripped) > 80:
            continue

        # Check for section-heading patterns:
        # "1. Introduction", "Section 2:", "A. Overview", "CHAPTER 3"
        heading_patterns = [
            r"^\d+[\.\)]\s+[A-Z]",           # "1. Something" or "1) Something"
            r"^[A-Z][a-z]+\s+\d+",            # "Section 1", "Chapter 2"
            r"^[A-Z]{2,}[\s:]+",              # "INTRODUCTION:", "OVERVIEW"
            r"^(?:Unit|Module|Topic|Section)\s", # Common syllabus headers
        ]

        for pattern in heading_patterns:
            if re.match(pattern, stripped):
                sections.append(stripped)
                break

    return sections


def load_text_as_framework(
    text: str,
    document_name: str,
    publisher: str = "",
    version: str = "",
    source_url: str = "",
    license_info: str = "",
    domain: str = "",
) -> dict:
    """
    Load plain text (not PDF) as a framework document.

    Useful for:
    - Framework data that comes as CSV/JSON and we convert to text.
    - Testing without needing actual PDF files.

    Returns the same structure as load_framework_document().
    """
    doc_id = re.sub(r"[^a-zA-Z0-9]", "-", document_name).strip("-").upper()[:30]

    # Split text into pseudo-pages (every ~2000 chars)
    page_size = 2000
    pages = []
    for i in range(0, len(text), page_size):
        chunk = text[i:i + page_size]
        if chunk.strip():
            sections = _detect_sections(chunk)
            pages.append({
                "page_number": len(pages) + 1,
                "text": chunk.strip(),
                "detected_sections": sections,
            })

    return {
        "document_id": doc_id,
        "document_name": document_name,
        "publisher": publisher,
        "version": version,
        "source_url": source_url,
        "license": license_info,
        "domain": domain,
        "total_pages": len(pages),
        "pages": pages,
        "full_text": text,
        "errors": [],
    }
