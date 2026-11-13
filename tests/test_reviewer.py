"""
tests/test_reviewer.py
======================
Unit tests for Agent 5: Reviewer Agent.

Verifies:
  - Rejection when evidence_id does not exist in evidence store.
  - Rejection when framework_id does not match the evidence record.
  - Rejection when resource URL is invalid.
  - Approval when evidence_id, framework_id, metadata, and resource URL are valid.
"""

import pytest
from backend.agents.reviewer import ReviewerAgent
from backend.core.schemas import Recommendation, EvidenceRecord, ReviewStatus


@pytest.fixture
def sample_evidence():
    return [
        EvidenceRecord(
            evidence_id="EV-001",
            framework_id="DS-011",
            document_name="NIST SP 800-181 Rev 1",
            document_version="Rev 1",
            source_url="https://csrc.nist.gov/publications/detail/sp/800-181/rev.1/final",
            page=12,
            section="MLOps and Deployment",
            text="Competency covering automated CI/CD pipelines and deployment for machine learning models.",
            similarity_score=0.88,
        ),
        EvidenceRecord(
            evidence_id="EV-002",
            framework_id="WD-011",
            document_name="ESCO Web Development Standards",
            document_version="1.2",
            source_url="https://esco.ec.europa.eu/",
            page=5,
            section="Accessibility Standards",
            text="Practitioners must implement WCAG 2.1 accessibility criteria across web user interfaces.",
            similarity_score=0.85,
        ),
    ]


class TestReviewerAgent:
    def test_approve_valid_recommendation(self, sample_evidence):
        """Valid recommendation with matching evidence should be APPROVED."""
        reviewer = ReviewerAgent()
        recs = [
            Recommendation(
                topic="MLOps and Deployment Pipelines",
                reason="Required for production ML lifecycle.",
                recommended_weight=10.0,
                level="Intermediate",
                resource="MLOps Zoomcamp",
                resource_url="https://github.com/DataTalksClub/mlops-zoomcamp",
                framework_id="DS-011",
                evidence_id="EV-001",
            )
        ]

        results = reviewer.review(recommendations=recs, evidence_records=sample_evidence)

        assert len(results) == 1
        assert results[0].status == ReviewStatus.APPROVED
        assert len(results[0].checks_failed) == 0
        assert "Valid retrieved framework evidence" in results[0].reason

    def test_reject_invalid_evidence_id(self, sample_evidence):
        """Recommendation citing non-existent evidence_id must be REJECTED."""
        reviewer = ReviewerAgent()
        recs = [
            Recommendation(
                topic="Hallucinated Topic",
                reason="No real evidence.",
                framework_id="DS-011",
                evidence_id="EV-NON-EXISTENT",
                resource="Some Course",
                resource_url="https://example.com/course",
            )
        ]

        results = reviewer.review(recommendations=recs, evidence_records=sample_evidence)

        assert len(results) == 1
        assert results[0].status == ReviewStatus.REJECTED
        assert any("does not exist" in check for check in results[0].checks_failed)

    def test_reject_mismatched_framework_id(self, sample_evidence):
        """Recommendation citing existing evidence but wrong framework_id must be REJECTED."""
        reviewer = ReviewerAgent()
        recs = [
            Recommendation(
                topic="Mismatched Competency",
                reason="Wrong ID attached.",
                framework_id="FAKE-ID-999",  # Does not match DS-011 in EV-001
                evidence_id="EV-001",
                resource="Some Guide",
                resource_url="https://example.com/guide",
            )
        ]

        results = reviewer.review(recommendations=recs, evidence_records=sample_evidence)

        assert len(results) == 1
        assert results[0].status == ReviewStatus.REJECTED
        assert any("mismatch" in check.lower() for check in results[0].checks_failed)

    def test_reject_invalid_resource_url(self, sample_evidence):
        """Recommendation with missing or malformed resource URL must be REJECTED."""
        reviewer = ReviewerAgent()
        recs = [
            Recommendation(
                topic="Accessibility",
                reason="Important topic.",
                framework_id="WD-011",
                evidence_id="EV-002",
                resource="Some Resource",
                resource_url="not-a-valid-url",
            )
        ]

        results = reviewer.review(recommendations=recs, evidence_records=sample_evidence)

        assert len(results) == 1
        assert results[0].status == ReviewStatus.REJECTED
        assert any("url" in check.lower() for check in results[0].checks_failed)
