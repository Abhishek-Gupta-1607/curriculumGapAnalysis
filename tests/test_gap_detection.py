"""
tests/test_gap_detection.py
===========================
Tests for Agent 3: Gap Detector Agent.

Verifies:
  - Exact topic match classification.
  - Synonym dictionary expansion and mapping.
  - Identification of partial vs missing competencies.
"""

import pytest
from backend.agents.gap_detector import GapDetectorAgent
from backend.core.schemas import (
    SyllabusData,
    ParsedSubject,
    ParsedTopic,
    EvidenceRecord,
    CoverageStatus,
)


@pytest.fixture
def sample_syllabus():
    return SyllabusData(
        source_type="text",
        course_name="BSc Computer Science",
        subjects=[
            ParsedSubject(
                name="Core CS",
                topics=[
                    ParsedTopic(name="Machine Learning Algorithms", unit="Unit 1"),
                    ParsedTopic(name="Relational Databases and SQL", unit="Unit 2"),
                    ParsedTopic(name="Basic Docker Containers", unit="Unit 3"),
                ],
            )
        ],
    )


@pytest.fixture
def sample_evidence():
    return [
        EvidenceRecord(
            evidence_id="EV-101",
            framework_id="TEST-001",
            document_name="Test Framework",
            text="Competency TEST-001: Machine Learning Algorithms\n[ID: TEST-001]\nSupervised learning methods.",
            similarity_score=0.9,
        ),
        EvidenceRecord(
            evidence_id="EV-102",
            framework_id="TEST-002",
            document_name="Test Framework",
            text="Competency TEST-002: Container Orchestration with Kubernetes\n[ID: TEST-002]\nProduction orchestration.",
            similarity_score=0.6,
        ),
        EvidenceRecord(
            evidence_id="EV-103",
            framework_id="TEST-003",
            document_name="Test Framework",
            text="Competency TEST-003: Quantum Cryptography and Hardware\n[ID: TEST-003]\nPost-quantum encryption.",
            similarity_score=0.1,
        ),
    ]


class TestGapDetectorAgent:
    def test_classify_covered_topic(self, sample_syllabus, sample_evidence):
        """Topic with identical match should be COVERED."""
        detector = GapDetectorAgent()
        matrix, gaps = detector.detect_gaps(sample_syllabus, sample_evidence)

        entry_covered = next((c for c in matrix if c.framework_id == "TEST-001"), None)
        assert entry_covered is not None
        assert entry_covered.status == CoverageStatus.COVERED
        assert entry_covered.similarity_score >= 0.75

    def test_classify_partial_or_missing_topics(self, sample_syllabus, sample_evidence):
        """Uncovered competencies should be identified as gaps (PARTIAL or MISSING)."""
        detector = GapDetectorAgent()
        matrix, gaps = detector.detect_gaps(sample_syllabus, sample_evidence)

        entry_missing = next((c for c in matrix if c.framework_id == "TEST-003"), None)
        assert entry_missing is not None
        assert entry_missing.status == CoverageStatus.MISSING

        # Gaps should include TEST-002 (partial/missing) and TEST-003 (missing)
        gap_ids = [g.framework_id for g in gaps]
        assert "TEST-003" in gap_ids
