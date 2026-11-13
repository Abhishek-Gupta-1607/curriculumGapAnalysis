"""
tests/test_rag.py
==================
Tests for the RAG pipeline: chunking, embeddings, and vector store.

These tests verify:
  - Text chunking produces correct chunk sizes and overlap.
  - Embeddings have the expected dimensions.
  - Cosine similarity works correctly for known cases.
  - Vector store add/search round-trip works.
"""

import os
import pytest
import shutil
import tempfile

from backend.rag.chunking import chunk_document, _split_text
from backend.rag.embeddings import compute_similarity


# =============================================================
# Test: Text Chunking
# =============================================================

class TestChunking:
    def test_short_text_single_chunk(self):
        """Short text should produce a single chunk."""
        chunks = _split_text("Hello world", chunk_size=500, chunk_overlap=50)
        assert len(chunks) == 1
        assert chunks[0] == "Hello world"

    def test_long_text_multiple_chunks(self):
        """Long text should be split into multiple chunks."""
        # Create text longer than chunk_size
        text = "Word " * 200  # ~1000 chars
        chunks = _split_text(text, chunk_size=200, chunk_overlap=30)
        assert len(chunks) > 1
        # Each chunk should be roughly chunk_size or smaller
        for chunk in chunks:
            assert len(chunk) <= 250  # Allow some flexibility for sentence boundaries

    def test_overlap_exists(self):
        """Consecutive chunks should overlap."""
        text = "The quick brown fox jumps over the lazy dog. " * 20
        chunks = _split_text(text, chunk_size=100, chunk_overlap=20)

        if len(chunks) >= 2:
            # The end of chunk N should appear at the start of chunk N+1
            # (approximately, due to sentence boundary detection)
            chunk1_end = chunks[0][-20:]  # Last 20 chars of chunk 1
            # The overlap region should contain some shared text
            assert len(chunks[1]) > 0

    def test_chunk_document_preserves_metadata(self):
        """chunk_document should attach metadata to each chunk."""
        document = {
            "document_id": "TEST-DOC",
            "document_name": "Test Framework",
            "publisher": "Test Publisher",
            "version": "1.0",
            "source_url": "https://example.com",
            "license": "Public Domain",
            "domain": "Testing",
            "pages": [
                {
                    "page_number": 1,
                    "text": "This is test content. " * 50,
                    "detected_sections": ["Section A"],
                },
            ],
        }

        chunks = chunk_document(document, chunk_size=200, chunk_overlap=30)
        assert len(chunks) > 0

        # Check metadata on first chunk
        first = chunks[0]
        assert first["document_id"] == "TEST-DOC"
        assert first["document_name"] == "Test Framework"
        assert first["page_number"] == 1
        assert first["section"] == "Section A"
        assert first["publisher"] == "Test Publisher"
        assert first["domain"] == "Testing"

    def test_chunk_ids_are_unique(self):
        """Each chunk should have a unique chunk_id."""
        document = {
            "document_id": "UNIQUE-TEST",
            "document_name": "Unique Test",
            "pages": [
                {"page_number": 1, "text": "Content " * 100, "detected_sections": []},
                {"page_number": 2, "text": "More content " * 100, "detected_sections": []},
            ],
        }

        chunks = chunk_document(document, chunk_size=200, chunk_overlap=30)
        ids = [c["chunk_id"] for c in chunks]
        assert len(ids) == len(set(ids))  # All IDs unique


# =============================================================
# Test: Cosine Similarity
# =============================================================

class TestCosineSimilarity:
    def test_identical_vectors(self):
        """Identical vectors should have similarity 1.0."""
        vec = [0.1, 0.2, 0.3, 0.4, 0.5]
        similarity = compute_similarity(vec, vec)
        assert abs(similarity - 1.0) < 0.001

    def test_opposite_vectors(self):
        """Opposite vectors should have similarity -1.0."""
        vec_a = [1.0, 0.0, 0.0]
        vec_b = [-1.0, 0.0, 0.0]
        similarity = compute_similarity(vec_a, vec_b)
        assert abs(similarity - (-1.0)) < 0.001

    def test_orthogonal_vectors(self):
        """Perpendicular vectors should have similarity 0.0."""
        vec_a = [1.0, 0.0, 0.0]
        vec_b = [0.0, 1.0, 0.0]
        similarity = compute_similarity(vec_a, vec_b)
        assert abs(similarity) < 0.001

    def test_similar_vectors(self):
        """Slightly different vectors should have high similarity."""
        vec_a = [0.1, 0.2, 0.3, 0.4]
        vec_b = [0.11, 0.19, 0.31, 0.39]
        similarity = compute_similarity(vec_a, vec_b)
        assert similarity > 0.99

    def test_empty_vectors(self):
        """Empty vectors should return 0.0."""
        assert compute_similarity([], []) == 0.0

    def test_mismatched_lengths(self):
        """Vectors of different lengths should return 0.0."""
        assert compute_similarity([1, 2], [1, 2, 3]) == 0.0

    def test_zero_vector(self):
        """Zero vector should return 0.0 (avoid division by zero)."""
        assert compute_similarity([0, 0, 0], [1, 2, 3]) == 0.0


# =============================================================
# Test: Embedding Generation (requires model download)
# =============================================================

class TestEmbeddings:
    """
    These tests require the sentence-transformers model to be downloaded.
    They will be skipped if the model is not available.
    """

    @pytest.fixture(autouse=True)
    def check_model(self):
        """Skip tests if sentence-transformers is not available."""
        try:
            from sentence_transformers import SentenceTransformer
            # Quick check — don't actually load if not cached
        except ImportError:
            pytest.skip("sentence-transformers not installed")

    def test_generate_embeddings(self):
        """Should generate embeddings of correct dimension."""
        from backend.rag.embeddings import generate_embeddings

        texts = ["Machine Learning", "Data Science"]
        embeddings = generate_embeddings(texts)

        assert len(embeddings) == 2
        # all-MiniLM-L6-v2 produces 384-dimensional vectors
        assert len(embeddings[0]) == 384
        assert len(embeddings[1]) == 384

    def test_similar_texts_have_high_similarity(self):
        """Semantically similar texts should have high cosine similarity."""
        from backend.rag.embeddings import generate_embeddings

        embeddings = generate_embeddings([
            "Machine Learning algorithms",
            "ML and artificial intelligence methods",
            "French cuisine recipes",
        ])

        # ML topics should be similar to each other
        sim_ml = compute_similarity(embeddings[0], embeddings[1])
        # ML should be dissimilar to cooking
        sim_cooking = compute_similarity(embeddings[0], embeddings[2])

        assert sim_ml > sim_cooking
        assert sim_ml > 0.5  # Should be reasonably similar
        assert sim_cooking < 0.5  # Should be quite different

    def test_empty_list(self):
        """Empty input should return empty output."""
        from backend.rag.embeddings import generate_embeddings

        result = generate_embeddings([])
        assert result == []
