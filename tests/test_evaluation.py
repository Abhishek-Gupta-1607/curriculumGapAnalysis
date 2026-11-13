"""
tests/test_evaluation.py
========================
Tests for evaluation metrics calculation and ground truth comparison.
"""

import pytest
from backend.services.evaluation_service import load_ground_truth


class TestEvaluationService:
    def test_load_ground_truth(self):
        """Ground truth file must exist and contain exactly 15 known missing gaps."""
        gt = load_ground_truth()
        assert "domains" in gt
        assert len(gt["domains"]) == 3

        total_gaps = sum(len(d["known_missing_ids"]) for d in gt["domains"].values())
        assert total_gaps == 15
        assert gt["total_known_gaps"] == 15

    def test_ground_truth_domain_keys(self):
        """Ground truth must have Data Science, Web Development, and Cloud and DevOps."""
        gt = load_ground_truth()
        domains = list(gt["domains"].keys())
        assert "Data Science" in domains
        assert "Web Development" in domains
        assert "Cloud and DevOps" in domains
