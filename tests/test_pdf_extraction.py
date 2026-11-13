"""
tests/test_pdf_extraction.py
=============================
Tests for the PDF text extraction service.

Note: These tests create temporary PDF files using reportlab
(if available) or test with text-based validation.
"""

import os
import pytest
import tempfile
from pathlib import Path

from backend.services.pdf_service import (
    extract_text_from_pdf,
    extract_text_from_bytes,
    validate_pdf_file,
)


def _create_test_pdf(text_content: str = "Hello World\nThis is a test PDF.") -> str:
    """
    Create a simple test PDF file using PyMuPDF.
    Returns the path to the temporary PDF.
    """
    import pymupdf as fitz

    pdf_path = os.path.join(tempfile.gettempdir(), "test_syllabus.pdf")
    doc = fitz.open()

    # Create a page with text
    page = doc.new_page()
    text_point = fitz.Point(72, 72)  # 1 inch from top-left
    page.insert_text(text_point, text_content, fontsize=12)

    doc.save(pdf_path)
    doc.close()

    return pdf_path


class TestExtractTextFromPdf:
    def test_basic_extraction(self):
        """Should extract text from a valid PDF."""
        pdf_path = _create_test_pdf("Unit 1: Introduction to Data Science")
        result = extract_text_from_pdf(pdf_path)

        assert result["filename"] == "test_syllabus.pdf"
        assert result["total_pages"] >= 1
        assert "Data Science" in result["full_text"]
        assert len(result["pages"]) >= 1
        assert result["pages"][0]["page_number"] == 1

        # Cleanup
        os.remove(pdf_path)

    def test_file_not_found(self):
        """Should raise FileNotFoundError for missing files."""
        with pytest.raises(FileNotFoundError):
            extract_text_from_pdf("/nonexistent/file.pdf")

    def test_not_a_pdf(self):
        """Should raise ValueError for non-PDF files."""
        # Create a temporary text file
        txt_path = os.path.join(tempfile.gettempdir(), "not_a.txt")
        with open(txt_path, "w") as f:
            f.write("This is not a PDF")

        with pytest.raises(ValueError):
            extract_text_from_pdf(txt_path)

        os.remove(txt_path)

    def test_multi_page_pdf(self):
        """Should extract text from multiple pages."""
        import pymupdf as fitz

        pdf_path = os.path.join(tempfile.gettempdir(), "multi_page.pdf")
        doc = fitz.open()

        for i in range(3):
            page = doc.new_page()
            page.insert_text(fitz.Point(72, 72), f"Page {i+1} content", fontsize=12)

        doc.save(pdf_path)
        doc.close()

        result = extract_text_from_pdf(pdf_path)
        assert result["total_pages"] == 3
        assert len(result["pages"]) == 3
        assert "Page 1" in result["pages"][0]["text"]
        assert "Page 3" in result["pages"][2]["text"]

        os.remove(pdf_path)


class TestExtractTextFromBytes:
    def test_bytes_extraction(self):
        """Should extract text from PDF bytes (simulating upload)."""
        import pymupdf as fitz

        # Create PDF in memory
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text(fitz.Point(72, 72), "Uploaded content", fontsize=12)
        pdf_bytes = doc.tobytes()
        doc.close()

        result = extract_text_from_bytes(pdf_bytes, filename="upload.pdf")
        assert result["filename"] == "upload.pdf"
        assert "Uploaded content" in result["full_text"]


class TestValidatePdfFile:
    def test_valid_pdf(self):
        """Should validate a good PDF."""
        pdf_path = _create_test_pdf()
        result = validate_pdf_file(pdf_path)

        assert result["valid"] is True
        assert result["total_pages"] >= 1
        assert result["error"] is None

        os.remove(pdf_path)

    def test_missing_file(self):
        """Should report invalid for missing files."""
        result = validate_pdf_file("/does/not/exist.pdf")
        assert result["valid"] is False
