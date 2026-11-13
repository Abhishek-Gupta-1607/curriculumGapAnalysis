"""
backend/services/pdf_service.py
================================
PDF text extraction service using PyMuPDF.

WHAT THIS FILE DOES:
  - Opens a PDF file.
  - Extracts text from every page.
  - Returns text with page numbers preserved.
  - Handles errors (corrupted files, empty pages).

WHY PyMuPDF?
  - Very fast PDF parsing (written in C).
  - Extracts text accurately with layout awareness.
  - Works completely offline.
  - Can extract page-by-page (needed for evidence citations).
  - Alternative: pdfplumber is slower; PyPDF2 has less accurate extraction.

USAGE:
  from backend.services.pdf_service import extract_text_from_pdf
  result = extract_text_from_pdf("path/to/syllabus.pdf")
  print(result["full_text"])
  print(result["pages"][0])  # text from page 1
"""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def extract_text_from_pdf(pdf_path: str) -> dict:
    """
    Extract all text from a PDF file.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        A dictionary with:
        {
            "filename": "syllabus.pdf",
            "total_pages": 5,
            "full_text": "All text concatenated...",
            "pages": [
                {"page_number": 1, "text": "Page 1 text..."},
                {"page_number": 2, "text": "Page 2 text..."},
            ],
            "errors": []
        }

    Raises:
        FileNotFoundError: If the PDF file doesn't exist.
        ValueError: If the file is not a valid PDF.
    """
    import pymupdf as fitz  # PyMuPDF — 'pymupdf' is the modern import name

    path = Path(pdf_path)

    # ── Validate the file exists ──
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    if not path.suffix.lower() == ".pdf":
        raise ValueError(f"File is not a PDF: {pdf_path}")

    result = {
        "filename": path.name,
        "total_pages": 0,
        "full_text": "",
        "pages": [],
        "errors": [],
    }

    try:
        # ── Open the PDF ──
        doc = fitz.open(str(path))
        result["total_pages"] = len(doc)

        all_text_parts = []

        # ── Extract text from each page ──
        for page_num in range(len(doc)):
            try:
                page = doc.load_page(page_num)
                # get_text() extracts text in reading order
                page_text = page.get_text()

                if page_text.strip():
                    all_text_parts.append(page_text)
                    result["pages"].append({
                        "page_number": page_num + 1,  # 1-indexed for humans
                        "text": page_text.strip(),
                    })
                else:
                    # Page has no extractable text (might be an image)
                    result["errors"].append(
                        f"Page {page_num + 1}: No extractable text (may be scanned/image)"
                    )

            except Exception as e:
                error_msg = f"Page {page_num + 1}: Extraction error - {str(e)}"
                result["errors"].append(error_msg)
                logger.warning(f"[PDF] {error_msg}")

        # ── Combine all page text ──
        result["full_text"] = "\n\n".join(all_text_parts)

        doc.close()

        logger.info(
            f"[PDF] Extracted {len(result['pages'])} pages from {path.name} "
            f"({len(result['full_text'])} chars)"
        )

    except Exception as exc:
        if "FileDataError" in type(exc).__name__:
            raise ValueError(f"Invalid or corrupted PDF file: {pdf_path}")
        else:
            raise ValueError(f"Error reading PDF: {str(exc)}")

    return result


def extract_text_from_bytes(pdf_bytes: bytes, filename: str = "upload.pdf") -> dict:
    """
    Extract text from PDF bytes (for file uploads via API).

    Args:
        pdf_bytes: Raw PDF file content as bytes.
        filename: Original filename for reference.

    Returns:
        Same structure as extract_text_from_pdf().
    """
    import pymupdf as fitz

    result = {
        "filename": filename,
        "total_pages": 0,
        "full_text": "",
        "pages": [],
        "errors": [],
    }

    try:
        # Open PDF from bytes (no file needed)
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        result["total_pages"] = len(doc)

        all_text_parts = []

        for page_num in range(len(doc)):
            try:
                page = doc.load_page(page_num)
                page_text = page.get_text()

                if page_text.strip():
                    all_text_parts.append(page_text)
                    result["pages"].append({
                        "page_number": page_num + 1,
                        "text": page_text.strip(),
                    })
                else:
                    result["errors"].append(
                        f"Page {page_num + 1}: No extractable text"
                    )
            except Exception as e:
                result["errors"].append(
                    f"Page {page_num + 1}: Extraction error - {str(e)}"
                )

        result["full_text"] = "\n\n".join(all_text_parts)
        doc.close()

        logger.info(
            f"[PDF] Extracted {len(result['pages'])} pages from upload "
            f"({len(result['full_text'])} chars)"
        )

    except Exception as e:
        raise ValueError(f"Error reading uploaded PDF: {str(e)}")

    return result


def validate_pdf_file(pdf_path: str) -> dict:
    """
    Quick validation of a PDF file without full text extraction.

    Returns:
        {
            "valid": True/False,
            "filename": "...",
            "total_pages": N,
            "file_size_kb": N,
            "error": None or "error message"
        }
    """
    import pymupdf as fitz

    path = Path(pdf_path)

    if not path.exists():
        return {"valid": False, "error": f"File not found: {pdf_path}"}

    if not path.suffix.lower() == ".pdf":
        return {"valid": False, "error": "File is not a PDF"}

    file_size_kb = path.stat().st_size / 1024

    try:
        doc = fitz.open(str(path))
        total_pages = len(doc)
        doc.close()

        return {
            "valid": True,
            "filename": path.name,
            "total_pages": total_pages,
            "file_size_kb": round(file_size_kb, 1),
            "error": None,
        }

    except Exception as e:
        return {
            "valid": False,
            "filename": path.name,
            "file_size_kb": round(file_size_kb, 1),
            "error": str(e),
        }
