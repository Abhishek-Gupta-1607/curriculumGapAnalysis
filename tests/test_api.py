"""
tests/test_api.py
=================
API Integration tests for FastAPI endpoints using TestClient.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


class TestAPIEndpoints:
    def test_root_endpoint(self):
        """Root should return online status."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "online"
        assert "mode" in data

    def test_health_check(self):
        """Health check endpoint should return 200 OK and healthy status."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"

    def test_list_samples(self):
        """Samples endpoint should return built-in sample syllabi."""
        response = client.get("/api/samples")
        assert response.status_code == 200
        samples = response.json()
        assert len(samples) >= 3
        domains = [s["domain"] for s in samples]
        assert "Data Science" in domains
        assert "Web Development" in domains
        assert "Cloud and DevOps" in domains
        assert "Agentic AI" in domains
        assert "Cybersecurity" in domains

    def test_list_runs(self):
        """Runs endpoint should return historical runs list."""
        response = client.get("/api/runs")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_frameworks(self):
        """Frameworks endpoint should list indexed frameworks and ChromaDB stats."""
        response = client.get("/api/frameworks")
        assert response.status_code == 200
        data = response.json()
        assert "frameworks" in data
        assert "chroma_stats" in data
        assert data["chroma_stats"]["total_documents"] >= 100
