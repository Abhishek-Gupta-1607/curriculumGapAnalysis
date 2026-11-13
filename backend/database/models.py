"""
backend/database/models.py
==========================
SQLAlchemy ORM models — one class per database table.

WHAT THIS FILE DOES:
  Defines the structure of every table in the SQLite database.
  Each class maps to a table, each attribute maps to a column.

HOW IT RELATES TO SCHEMAS:
  - schemas.py (Pydantic) → data validation and API contracts.
  - models.py (SQLAlchemy) → database storage and queries.
  They look similar but serve different purposes.

TABLE OVERVIEW:
  AnalysisRun      → one row per analysis execution
  AgentEvent       → one row per agent invocation (tracing)
  SyllabusDocument → uploaded/input syllabus metadata
  FrameworkDocument → ingested framework document metadata
  RetrievedEvidence → evidence chunks from framework retrieval
  RecommendationRecord → recommendations (pre-review and post-review)
  EvaluationRecord → evaluation metrics per run
  ReportRecord     → generated report file paths
"""

from datetime import datetime

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Text,
    DateTime,
    JSON,
    ForeignKey,
    Boolean,
)
from sqlalchemy.orm import relationship

from backend.database.db import Base


class AnalysisRun(Base):
    """
    Represents one complete analysis execution.

    Every time a user uploads a syllabus and runs the pipeline,
    one AnalysisRun row is created. All other records link back
    to this via run_id.
    """
    __tablename__ = "analysis_runs"

    id = Column(String, primary_key=True, doc="Run ID, e.g. RUN-20261113-120530")
    domain = Column(String, nullable=False, doc="Analysis domain")
    status = Column(
        String, default="PENDING", doc="PENDING, RUNNING, COMPLETED, FAILED"
    )
    mode = Column(String, default="OFFLINE", doc="OFFLINE or LLM_ASSISTED")
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Store the complete workflow state as JSON
    # This is the authoritative record of the entire analysis
    shared_state_json = Column(Text, nullable=True, doc="Full WorkflowState as JSON")

    # ── Relationships (for easy querying) ──
    events = relationship("AgentEvent", back_populates="run", cascade="all, delete-orphan")
    syllabus = relationship(
        "SyllabusDocument", back_populates="run", uselist=False, cascade="all, delete-orphan"
    )
    evidence_records = relationship(
        "RetrievedEvidence", back_populates="run", cascade="all, delete-orphan"
    )
    recommendation_records = relationship(
        "RecommendationRecord", back_populates="run", cascade="all, delete-orphan"
    )
    evaluation = relationship(
        "EvaluationRecord", back_populates="run", uselist=False, cascade="all, delete-orphan"
    )
    report = relationship(
        "ReportRecord", back_populates="run", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<AnalysisRun {self.id} [{self.status}]>"


class AgentEvent(Base):
    """
    Records one agent's execution within a pipeline run.

    This is how we trace what happened: which agent ran, how long
    it took, what it produced, and whether it failed.
    """
    __tablename__ = "agent_events"

    id = Column(String, primary_key=True, doc="Event ID, e.g. EVT-001")
    run_id = Column(String, ForeignKey("analysis_runs.id"), nullable=False)
    step_number = Column(Integer, nullable=False, doc="Pipeline step (1-6)")
    agent_name = Column(String, nullable=False, doc="Name of the agent")
    status = Column(String, nullable=False, doc="STARTED, COMPLETED, FAILED")
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True, doc="Execution time in milliseconds")
    input_summary = Column(Text, nullable=True, doc="Brief description of input")
    output_summary = Column(Text, nullable=True, doc="Brief description of output")
    token_usage = Column(Integer, nullable=True, doc="LLM tokens used (0 if offline)")
    error_details = Column(Text, nullable=True, doc="Error message if failed")
    evidence_ids = Column(JSON, nullable=True, doc="List of evidence IDs involved")

    # ── Relationship ──
    run = relationship("AnalysisRun", back_populates="events")

    def __repr__(self):
        return f"<AgentEvent {self.id} [{self.agent_name}: {self.status}]>"


class SyllabusDocument(Base):
    """
    Metadata and parsed content of an uploaded syllabus.
    """
    __tablename__ = "syllabus_documents"

    id = Column(String, primary_key=True)
    run_id = Column(String, ForeignKey("analysis_runs.id"), nullable=False)
    filename = Column(String, nullable=True, doc="Original filename")
    source_type = Column(String, nullable=False, doc="'pdf' or 'text'")
    raw_text = Column(Text, nullable=True, doc="Extracted raw text")
    parsed_data = Column(JSON, nullable=True, doc="Parsed syllabus as JSON")
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    run = relationship("AnalysisRun", back_populates="syllabus")


class FrameworkDocument(Base):
    """
    Metadata for an ingested industry framework document.

    This is NOT per-run — framework documents are ingested once
    and reused across all analyses.
    """
    __tablename__ = "framework_documents"

    id = Column(String, primary_key=True, doc="e.g. NICE-SP800-181")
    name = Column(String, nullable=False, doc="Document title")
    publisher = Column(String, nullable=False, doc="e.g. NIST, European Commission")
    version = Column(String, default="")
    source_url = Column(String, default="", doc="Where to download the document")
    license = Column(String, default="", doc="e.g. Public Domain, CC BY 4.0")
    domain = Column(String, default="", doc="Primary domain")
    download_date = Column(DateTime, nullable=True)
    chunk_count = Column(Integer, default=0, doc="Number of indexed chunks")
    ingestion_status = Column(
        String, default="PENDING", doc="PENDING, INGESTING, COMPLETED, FAILED"
    )

    def __repr__(self):
        return f"<FrameworkDocument {self.id}: {self.name}>"


class RetrievedEvidence(Base):
    """
    An evidence record retrieved from the vector store during analysis.
    Linked to a specific run.
    """
    __tablename__ = "retrieved_evidence"

    id = Column(String, primary_key=True, doc="Evidence ID, e.g. EV-001")
    run_id = Column(String, ForeignKey("analysis_runs.id"), nullable=False)
    framework_doc_id = Column(String, nullable=True, doc="Reference to FrameworkDocument")
    framework_id = Column(String, nullable=False, doc="Competency ID")
    page = Column(Integer, nullable=True)
    section = Column(String, default="")
    text = Column(Text, nullable=False, doc="Retrieved text passage")
    similarity_score = Column(Float, default=0.0)

    run = relationship("AnalysisRun", back_populates="evidence_records")


class RecommendationRecord(Base):
    """
    A recommendation stored with its review status.
    """
    __tablename__ = "recommendations"

    id = Column(String, primary_key=True, doc="Recommendation ID")
    run_id = Column(String, ForeignKey("analysis_runs.id"), nullable=False)
    topic = Column(String, nullable=False)
    reason = Column(Text, default="")
    recommended_weight = Column(Float, nullable=True)
    level = Column(String, default="Intermediate")
    resource_name = Column(String, default="")
    resource_url = Column(String, default="")
    framework_id = Column(String, default="")
    evidence_id = Column(String, default="")
    review_status = Column(String, nullable=True, doc="APPROVED or REJECTED")
    review_reason = Column(Text, nullable=True)

    run = relationship("AnalysisRun", back_populates="recommendation_records")


class EvaluationRecord(Base):
    """
    Evaluation metrics for a specific analysis run.
    """
    __tablename__ = "evaluation_records"

    id = Column(String, primary_key=True)
    run_id = Column(String, ForeignKey("analysis_runs.id"), nullable=False)
    domain = Column(String, nullable=False)
    total_known_gaps = Column(Integer, default=0)
    correctly_detected = Column(Integer, default=0)
    false_positives = Column(Integer, default=0)
    false_negatives = Column(Integer, default=0)
    precision_score = Column(Float, default=0.0)
    recall_score = Column(Float, default=0.0)
    f1_score = Column(Float, default=0.0)
    detection_rate = Column(Float, default=0.0)
    citation_coverage_before = Column(Float, default=0.0)
    citation_coverage_after = Column(Float, default=0.0)

    run = relationship("AnalysisRun", back_populates="evaluation")


class ReportRecord(Base):
    """
    File paths for generated reports.
    """
    __tablename__ = "report_records"

    id = Column(String, primary_key=True)
    run_id = Column(String, ForeignKey("analysis_runs.id"), nullable=False)
    pdf_path = Column(String, nullable=True)
    json_path = Column(String, nullable=True)
    generated_at = Column(DateTime, default=datetime.utcnow)

    run = relationship("AnalysisRun", back_populates="report")
