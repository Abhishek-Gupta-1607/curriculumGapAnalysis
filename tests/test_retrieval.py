"""
tests/test_retrieval.py
========================
Tests for RAG retrieval and framework ingestion verification.
"""

import pytest
from backend.rag.embeddings import generate_single_embedding
from backend.rag.vector_store import (
    get_collection_stats,
    search_similar,
)


class TestVectorRetrieval:
    def test_framework_collection_has_documents(self):
        """Ensure ChromaDB has indexed framework documents."""
        stats = get_collection_stats()
        assert stats["total_documents"] >= 100
        assert "Data Science" in stats["domains"]
        assert "Web Development" in stats["domains"]
        assert "Cloud and DevOps" in stats["domains"]

    def test_retrieve_data_science_evidence(self):
        """Querying for MLOps should return DS-011 evidence."""
        query = "MLOps and automated model deployment pipelines"
        vec = generate_single_embedding(query)
        results = search_similar(vec, top_k=3, domain_filter="Data Science")

        assert len(results) > 0
        top_meta = results[0]["metadata"]
        assert top_meta["domain"] == "Data Science"
        assert top_meta["framework_id"] == "DS-011"
        assert top_meta["page_number"] is not None
        assert "MLOps" in results[0]["text"]

    def test_retrieve_web_development_evidence(self):
        """Querying for WCAG Accessibility should return WD-011 evidence."""
        query = "Web accessibility WCAG standards and screen reader support"
        vec = generate_single_embedding(query)
        results = search_similar(vec, top_k=3, domain_filter="Web Development")

        assert len(results) > 0
        top_meta = results[0]["metadata"]
        assert top_meta["domain"] == "Web Development"
        assert top_meta["framework_id"] == "WD-011"
        assert "Accessibility" in results[0]["text"] or "WCAG" in results[0]["text"]

    def test_retrieve_cloud_devops_evidence(self):
        """Querying for Kubernetes should return CD-011 evidence."""
        query = "Kubernetes pods services deployments container orchestration"
        vec = generate_single_embedding(query)
        results = search_similar(vec, top_k=3, domain_filter="Cloud and DevOps")

        assert len(results) > 0
        top_meta = results[0]["metadata"]
        assert top_meta["domain"] == "Cloud and DevOps"
        assert top_meta["framework_id"] == "CD-011"
        assert "Kubernetes" in results[0]["text"]
