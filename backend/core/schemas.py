"""
backend/core/schemas.py
=======================
All Pydantic models for the Curriculum Gap Analysis Pipeline.

These models define the shape of data flowing between agents.
They provide automatic validation, serialisation (to JSON), and
clear documentation of every field.

WHY PYDANTIC?
  - Validates data types automatically (catches bugs early).
  - Converts to/from JSON with one method call.
  - Serves as living documentation of data structures.
  - Works directly with FastAPI for request/response validation.

ORGANISATION:
  1. Syllabus models        → output of Agent 1 (Parser)
  2. Evidence models        → output of Agent 2 (Retriever)
  3. Coverage models        → output of Agent 3 (Gap Detector)
  4. Recommendation models  → output of Agent 4 (Recommender)
  5. Review models          → output of Agent 5 (Reviewer)
  6. WorkflowState          → shared state passed between all agents
  7. Request/Response models → FastAPI API contracts
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# =============================================================
# 1. SYLLABUS MODELS  (Agent 1 – Syllabus Parser)
# =============================================================

class ParsedTopic(BaseModel):
    """A single topic extracted from the syllabus."""
    name: str = Field(..., description="Topic name as it appears in the syllabus")
    unit: str = Field(default="", description="Unit or module name (e.g. 'Unit 1')")
    subtopics: list[str] = Field(
        default_factory=list,
        description="List of subtopic names under this topic",
    )
    official_weight: Optional[float] = Field(
        default=None,
        description="Official marks/hours/percentage from syllabus. None if not available.",
    )


class ParsedSubject(BaseModel):
    """A subject or course within the syllabus."""
    name: str = Field(..., description="Subject or course name")
    topics: list[ParsedTopic] = Field(
        default_factory=list,
        description="List of topics in this subject",
    )


class SyllabusData(BaseModel):
    """Complete parsed syllabus output from Agent 1."""
    source_type: str = Field(..., description="'pdf' or 'text'")
    filename: Optional[str] = Field(
        default=None, description="Original filename if uploaded"
    )
    course_name: str = Field(default="", description="Overall course/programme name")
    subjects: list[ParsedSubject] = Field(
        default_factory=list,
        description="List of subjects in the syllabus",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Ambiguous or unreadable content flags",
    )

    @property
    def all_topics(self) -> list[ParsedTopic]:
        """Flatten all topics across all subjects into one list."""
        topics = []
        for subject in self.subjects:
            topics.extend(subject.topics)
        return topics

    @property
    def topic_names(self) -> list[str]:
        """Get just the topic name strings for easy searching."""
        return [t.name for t in self.all_topics]


# =============================================================
# 2. EVIDENCE MODELS  (Agent 2 – Skills Retriever)
# =============================================================

class EvidenceRecord(BaseModel):
    """
    A single piece of evidence retrieved from an industry framework.

    Every evidence record traces back to a real document, page, and section.
    This is what makes our recommendations verifiable.
    """
    evidence_id: str = Field(..., description="Unique ID, e.g. 'EV-001'")
    framework_id: str = Field(
        ..., description="Competency ID within the framework, e.g. 'NICE-DA-001'"
    )
    document_name: str = Field(..., description="Name of the framework document")
    document_version: str = Field(default="", description="Document version")
    source_url: str = Field(default="", description="URL where document can be found")
    page: Optional[int] = Field(
        default=None, description="Page number in the source document"
    )
    section: str = Field(default="", description="Section heading in the document")
    text: str = Field(..., description="The actual retrieved text passage")
    similarity_score: float = Field(
        default=0.0,
        description="Cosine similarity score from the retrieval query",
    )


# =============================================================
# 3. COVERAGE MODELS  (Agent 3 – Gap Detector)
# =============================================================

class CoverageStatus(str, Enum):
    """Classification of how well a framework skill is covered."""
    COVERED = "COVERED"     # similarity >= covered_threshold (default 0.75)
    PARTIAL = "PARTIAL"     # similarity >= partial_threshold (default 0.45)
    MISSING = "MISSING"     # similarity < partial_threshold


class CoverageEntry(BaseModel):
    """
    One row in the coverage matrix.

    Maps a framework competency to its best-matching syllabus topic
    and records how well it is covered.
    """
    framework_skill: str = Field(..., description="Competency name from the framework")
    framework_id: str = Field(..., description="Competency ID from the framework")
    matching_topic: Optional[str] = Field(
        default=None,
        description="Best matching syllabus topic name (None if MISSING)",
    )
    similarity_score: float = Field(
        ..., description="Cosine similarity between framework skill and best match"
    )
    status: CoverageStatus = Field(..., description="COVERED, PARTIAL, or MISSING")
    evidence_id: str = Field(..., description="ID of the evidence record")
    reasoning: str = Field(
        default="",
        description="Why this classification was made",
    )


class GapRecord(BaseModel):
    """A confirmed gap (MISSING or PARTIAL competency)."""
    skill: str = Field(..., description="Framework competency name")
    framework_id: str = Field(..., description="Framework competency ID")
    status: CoverageStatus = Field(..., description="PARTIAL or MISSING")
    evidence_id: str = Field(..., description="Supporting evidence ID")
    similarity_score: float = Field(default=0.0)


# =============================================================
# 4. RECOMMENDATION MODELS  (Agent 4 – Resource Recommender)
# =============================================================

class Recommendation(BaseModel):
    """
    A suggestion to add a topic to the curriculum.

    Each recommendation has:
    - What to add (topic, weight, level).
    - Why to add it (reason, framework citation).
    - Where to learn it (resource, URL).
    """
    recommendation_id: str = Field(
        default_factory=lambda: f"REC-{uuid.uuid4().hex[:6].upper()}",
        description="Unique recommendation ID",
    )
    topic: str = Field(..., description="Suggested curriculum topic")
    reason: str = Field(..., description="Why this topic should be added")
    recommended_weight: Optional[float] = Field(
        default=None, description="Suggested weight (clearly labelled as suggested)"
    )
    weight_type: str = Field(
        default="Suggested",
        description="Always 'Suggested' — never presented as official",
    )
    level: str = Field(
        default="Intermediate",
        description="Learning level: Beginner, Intermediate, or Advanced",
    )
    resource: str = Field(default="", description="Recommended learning resource name")
    resource_url: str = Field(default="", description="URL of the learning resource")
    framework_id: str = Field(
        ..., description="Framework competency ID that justifies this"
    )
    evidence_id: str = Field(
        ..., description="Evidence record ID from the retrieval step"
    )


# =============================================================
# 5. REVIEW MODELS  (Agent 5 – Reviewer)
# =============================================================

class ReviewStatus(str, Enum):
    """Reviewer decision."""
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ReviewResult(BaseModel):
    """
    The Reviewer's verdict on a single recommendation.

    The Reviewer validates that every recommendation has real evidence
    backing it. It checks evidence_id, framework_id, and metadata.
    """
    recommendation_id: str = Field(
        ..., description="ID of the recommendation being reviewed"
    )
    topic: str = Field(..., description="Topic name for easy reference")
    evidence_id: str = Field(..., description="Evidence ID that was checked")
    status: ReviewStatus = Field(..., description="APPROVED or REJECTED")
    reason: str = Field(
        ..., description="Why it was approved or rejected"
    )
    checks_passed: list[str] = Field(
        default_factory=list,
        description="List of validation checks that passed",
    )
    checks_failed: list[str] = Field(
        default_factory=list,
        description="List of validation checks that failed",
    )


# =============================================================
# 6. WORKFLOW STATE  (Shared between all agents)
# =============================================================

class WorkflowState(BaseModel):
    """
    The shared state object that flows through the entire pipeline.

    Every agent reads from and writes to this state.
    It is persisted to the database after each agent completes.

    KEY DESIGN DECISIONS:
    - One WorkflowState per analysis run (isolated by run_id).
    - Pydantic validates the structure at every stage.
    - JSON serialisation allows storage in SQLite and transmission via API.
    """
    # ── Run metadata ──
    run_id: str = Field(..., description="Unique run identifier, e.g. 'RUN-20261113-001'")
    domain: str = Field(default="", description="Analysis domain, e.g. 'Data Science'")
    status: str = Field(
        default="PENDING",
        description="PENDING, RUNNING, COMPLETED, or FAILED",
    )
    mode: str = Field(default="OFFLINE", description="OFFLINE or LLM_ASSISTED")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)
    current_step: int = Field(
        default=0, description="Current step in the pipeline (1-6)"
    )
    current_agent: str = Field(
        default="", description="Name of the currently running agent"
    )

    # ── Agent 1 output: parsed syllabus ──
    syllabus_data: Optional[SyllabusData] = Field(
        default=None, description="Structured syllabus from the Parser Agent"
    )

    # ── Agent 2 output: retrieved evidence ──
    framework_evidence: list[EvidenceRecord] = Field(
        default_factory=list,
        description="Evidence records from industry frameworks",
    )

    # ── Agent 3 output: coverage analysis ──
    coverage_matrix: list[CoverageEntry] = Field(
        default_factory=list,
        description="Coverage classification for each framework skill",
    )
    gaps: list[GapRecord] = Field(
        default_factory=list,
        description="Confirmed gaps (MISSING + PARTIAL skills)",
    )

    # ── Agent 4 output: recommendations ──
    recommendations: list[Recommendation] = Field(
        default_factory=list,
        description="Suggested curriculum additions",
    )

    # ── Agent 5 output: reviewer results ──
    reviewer_results: list[ReviewResult] = Field(
        default_factory=list,
        description="Reviewer verdicts on each recommendation",
    )

    # ── Error tracking ──
    errors: list[str] = Field(
        default_factory=list,
        description="Error messages from any stage",
    )

    # ── Agent 6 output: final report summary ──
    final_report: dict = Field(
        default_factory=dict,
        description="Final report metadata (paths, stats)",
    )

    # ── Convenience properties ──

    @property
    def approved_recommendations(self) -> list[Recommendation]:
        """Get only the recommendations that passed review."""
        approved_ids = {
            r.recommendation_id
            for r in self.reviewer_results
            if r.status == ReviewStatus.APPROVED
        }
        return [r for r in self.recommendations if r.recommendation_id in approved_ids]

    @property
    def rejected_recommendations(self) -> list[Recommendation]:
        """Get recommendations that failed review."""
        rejected_ids = {
            r.recommendation_id
            for r in self.reviewer_results
            if r.status == ReviewStatus.REJECTED
        }
        return [r for r in self.recommendations if r.recommendation_id in rejected_ids]

    @property
    def evidence_lookup(self) -> dict[str, EvidenceRecord]:
        """Build a dict for quick evidence lookup by evidence_id."""
        return {e.evidence_id: e for e in self.framework_evidence}

    @property
    def statistics(self) -> dict:
        """Summary statistics for the report."""
        total = len(self.coverage_matrix)
        covered = sum(
            1 for c in self.coverage_matrix if c.status == CoverageStatus.COVERED
        )
        partial = sum(
            1 for c in self.coverage_matrix if c.status == CoverageStatus.PARTIAL
        )
        missing = sum(
            1 for c in self.coverage_matrix if c.status == CoverageStatus.MISSING
        )
        return {
            "total_framework_skills": total,
            "covered": covered,
            "partial": partial,
            "missing": missing,
            "total_recommendations": len(self.recommendations),
            "approved_recommendations": len(self.approved_recommendations),
            "rejected_recommendations": len(self.rejected_recommendations),
        }


# =============================================================
# 7. API REQUEST / RESPONSE MODELS
# =============================================================

class AnalyzeRequest(BaseModel):
    """Request body for POST /api/analyze (text input)."""
    syllabus_text: str = Field(..., description="Pasted syllabus text")
    domain: str = Field(default="General", description="Analysis domain")
    covered_threshold: Optional[float] = Field(default=None)
    partial_threshold: Optional[float] = Field(default=None)


class AnalyzeResponse(BaseModel):
    """Response from POST /api/analyze."""
    run_id: str
    status: str
    message: str


class RunSummary(BaseModel):
    """Summary of an analysis run for listing."""
    run_id: str
    domain: str
    status: str
    mode: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    total_gaps: int = 0
    approved_recommendations: int = 0


class HealthResponse(BaseModel):
    """Response from GET /api/health."""
    status: str = "healthy"
    mode: str = "OFFLINE"
    version: str = "1.0.0"
    database: str = "connected"


class EvaluationMetrics(BaseModel):
    """Evaluation results for a single domain."""
    domain: str
    total_known_gaps: int
    correctly_detected: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float
    f1_score: float
    detection_rate: float
    suggestions_before_review: int = 0
    suggestions_after_review: int = 0
    citation_coverage_before: float = 0.0
    citation_coverage_after: float = 0.0


class OverallEvaluation(BaseModel):
    """Complete evaluation across all domains."""
    per_domain: list[EvaluationMetrics]
    overall: EvaluationMetrics
    limitation: str = (
        "The evaluation uses a small, author-designed benchmark of three syllabi "
        "and 15 known gaps. Results demonstrate performance on these test cases "
        "and do not establish generalisation to all academic curricula."
    )
