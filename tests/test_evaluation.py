"""
tests/test_evaluation.py
========================
Tests for evaluation metrics calculation and ground truth comparison.
"""

import pytest
from backend.services.evaluation_service import load_ground_truth


class TestEvaluationService:
    def test_load_ground_truth(self):
        """Ground truth file must exist and contain exactly 40 known missing gaps across 8 domains."""
        gt = load_ground_truth()
        assert "domains" in gt
        assert len(gt["domains"]) == 8

        total_gaps = sum(len(d["known_missing_ids"]) for d in gt["domains"].values())
        assert total_gaps == 40
        assert gt["total_known_gaps"] == 40

    def test_ground_truth_domain_keys(self):
        """Ground truth must have all 8 supported academic and industry domains."""
        gt = load_ground_truth()
        domains = list(gt["domains"].keys())
        expected_domains = [
            "Data Science",
            "Web Development",
            "Cloud and DevOps",
            "Agentic AI",
            "Cybersecurity",
            "Machine Learning",
            "Deep Learning",
            "Full Stack"
        ]
        for d in expected_domains:
            assert d in domains, f"Missing domain '{d}' in ground_truth.json"
