"""
tests/test_schemas.py
=====================
Tests for Pydantic schema validation.

Tests that our data models:
  - Accept valid data correctly.
  - Reject invalid data with clear errors.
  - Serialise to/from JSON correctly.
  - Compute convenience properties accurately.
"""

import pytest
from datetime import datetime

from backend.core.schemas import (
    ParsedTopic,
    ParsedSubject,
    SyllabusData,
    EvidenceRecord,
    CoverageEntry,
    CoverageStatus,
    GapRecord,
    Recommendation,
    ReviewResult,
    ReviewStatus,
    WorkflowState,
)


# =============================================================
# Test 1: ParsedTopic creation and optional weights
# =============================================================

class TestParsedTopic:
    def test_create_with_weight(self):
        """Topic with an official weight should preserve it."""
        topic = ParsedTopic(
            name="Linear Regression",
            unit="Unit 1",
            subtopics=["Simple Regression", "Multiple Regression"],
            official_weight=15.0,
        )
        assert topic.name == "Linear Regression"
        assert topic.official_weight == 15.0
        assert len(topic.subtopics) == 2

    def test_create_without_weight(self):
        """Topic without weight should default to None (not invented)."""
        topic = ParsedTopic(name="Data Cleaning", unit="Unit 2")
        assert topic.official_weight is None
        assert topic.subtopics == []

    def test_requires_name(self):
        """Topic must have a name — Pydantic should reject missing name."""
        with pytest.raises(Exception):
            ParsedTopic()


# =============================================================
# Test 2: SyllabusData flattening
# =============================================================

class TestSyllabusData:
    def test_all_topics_flattened(self):
        """all_topics property should flatten topics from all subjects."""
        syllabus = SyllabusData(
            source_type="text",
            course_name="BSc Data Science",
            subjects=[
                ParsedSubject(
                    name="Subject A",
                    topics=[
                        ParsedTopic(name="Topic 1", unit="U1"),
                        ParsedTopic(name="Topic 2", unit="U1"),
                    ],
                ),
                ParsedSubject(
                    name="Subject B",
                    topics=[
                        ParsedTopic(name="Topic 3", unit="U2"),
                    ],
                ),
            ],
        )
        assert len(syllabus.all_topics) == 3
        assert syllabus.topic_names == ["Topic 1", "Topic 2", "Topic 3"]

    def test_empty_syllabus(self):
        """Empty syllabus should have no topics."""
        syllabus = SyllabusData(source_type="text")
        assert len(syllabus.all_topics) == 0
        assert syllabus.topic_names == []


# =============================================================
# Test 3: EvidenceRecord validation
# =============================================================

class TestEvidenceRecord:
    def test_create_valid_evidence(self):
        """Valid evidence record should preserve all fields."""
        evidence = EvidenceRecord(
            evidence_id="EV-001",
            framework_id="NICE-DA-001",
            document_name="NIST SP 800-181",
            document_version="Rev 1",
            source_url="https://csrc.nist.gov/...",
            page=12,
            section="Data Analysis",
            text="The ability to analyse data...",
            similarity_score=0.85,
        )
        assert evidence.evidence_id == "EV-001"
        assert evidence.page == 12

    def test_requires_evidence_id(self):
        """Evidence without an ID should fail validation."""
        with pytest.raises(Exception):
            EvidenceRecord(
                framework_id="NICE-001",
                document_name="Test",
                text="Test text",
            )


# =============================================================
# Test 4: CoverageEntry classification
# =============================================================

class TestCoverageEntry:
    def test_covered_status(self):
        """COVERED status should be a valid enum value."""
        entry = CoverageEntry(
            framework_skill="Machine Learning",
            framework_id="NICE-001",
            matching_topic="ML Fundamentals",
            similarity_score=0.85,
            status=CoverageStatus.COVERED,
            evidence_id="EV-001",
        )
        assert entry.status == CoverageStatus.COVERED
        assert entry.status.value == "COVERED"

    def test_missing_status(self):
        """MISSING skills should have no matching topic."""
        entry = CoverageEntry(
            framework_skill="Quantum Computing",
            framework_id="NICE-099",
            matching_topic=None,
            similarity_score=0.12,
            status=CoverageStatus.MISSING,
            evidence_id="EV-099",
        )
        assert entry.status == CoverageStatus.MISSING
        assert entry.matching_topic is None


# =============================================================
# Test 5: WorkflowState lifecycle
# =============================================================

class TestWorkflowState:
    def test_create_fresh_state(self):
        """New state should have empty agent outputs."""
        state = WorkflowState(run_id="RUN-TEST-001", domain="Data Science")
        assert state.status == "PENDING"
        assert state.mode == "OFFLINE"
        assert state.syllabus_data is None
        assert state.framework_evidence == []
        assert state.coverage_matrix == []
        assert state.gaps == []
        assert state.recommendations == []
        assert state.reviewer_results == []
        assert state.errors == []

    def test_json_serialisation(self):
        """State should serialise to JSON and back without data loss."""
        state = WorkflowState(run_id="RUN-TEST-002", domain="Web Development")
        json_str = state.model_dump_json()
        restored = WorkflowState.model_validate_json(json_str)
        assert restored.run_id == "RUN-TEST-002"
        assert restored.domain == "Web Development"

    def test_approved_recommendations_property(self):
        """approved_recommendations should filter by reviewer results."""
        state = WorkflowState(
            run_id="RUN-TEST-003",
            domain="Test",
            recommendations=[
                Recommendation(
                    recommendation_id="REC-001",
                    topic="MLOps",
                    reason="Test",
                    framework_id="F-001",
                    evidence_id="EV-001",
                ),
                Recommendation(
                    recommendation_id="REC-002",
                    topic="Docker",
                    reason="Test",
                    framework_id="F-002",
                    evidence_id="EV-002",
                ),
            ],
            reviewer_results=[
                ReviewResult(
                    recommendation_id="REC-001",
                    topic="MLOps",
                    evidence_id="EV-001",
                    status=ReviewStatus.APPROVED,
                    reason="Valid evidence",
                ),
                ReviewResult(
                    recommendation_id="REC-002",
                    topic="Docker",
                    evidence_id="EV-002",
                    status=ReviewStatus.REJECTED,
                    reason="Invalid evidence ID",
                ),
            ],
        )
        approved = state.approved_recommendations
        rejected = state.rejected_recommendations
        assert len(approved) == 1
        assert approved[0].topic == "MLOps"
        assert len(rejected) == 1
        assert rejected[0].topic == "Docker"

    def test_statistics_property(self):
        """statistics should compute counts from coverage matrix."""
        state = WorkflowState(
            run_id="RUN-TEST-004",
            domain="Test",
            coverage_matrix=[
                CoverageEntry(
                    framework_skill="A", framework_id="F-1",
                    similarity_score=0.9, status=CoverageStatus.COVERED,
                    evidence_id="EV-1",
                ),
                CoverageEntry(
                    framework_skill="B", framework_id="F-2",
                    similarity_score=0.5, status=CoverageStatus.PARTIAL,
                    evidence_id="EV-2",
                ),
                CoverageEntry(
                    framework_skill="C", framework_id="F-3",
                    similarity_score=0.2, status=CoverageStatus.MISSING,
                    evidence_id="EV-3",
                ),
            ],
        )
        stats = state.statistics
        assert stats["total_framework_skills"] == 3
        assert stats["covered"] == 1
        assert stats["partial"] == 1
        assert stats["missing"] == 1
