"""
backend/agents/curriculum_coordinator.py
========================================
AGENT 6: CURRICULUM COORDINATOR

PURPOSE:
  Orchestrate the end-to-end multi-agent curriculum gap analysis pipeline.

TECHNOLOGY:
  - Microsoft Semantic Kernel (SK) SequentialOrchestration & Agents
  - Pydantic WorkflowState shared memory
  - SQLAlchemy & SQLite persistence
  - Execution Tracing Module (backend/core/tracing.py)

SEQUENTIAL EXECUTION PIPELINE:
  Step 1: Syllabus Parser Agent
          (Extracts structured subjects, units, topics, and weights)
  Step 2: Skills Framework Retrieval Agent
          (Queries ChromaDB RAG vector store for verified industry evidence)
  Step 3: Gap Detector Agent
          (Calculates semantic similarity & classifies into COVERED, PARTIAL, MISSING)
  Step 4: Resource Recommender Agent
          (Formulates proposed curriculum additions and learning resources)
  Step 5: Reviewer Agent
          (Deterministically audits citations, rejects unverified suggestions)
  Step 6: Coordinator Synthesis & State Finalization
          (Collates approved suggestions, computes statistics, and persists run state)

ERROR HANDLING:
  - Validates stage prerequisites before execution.
  - Records real-time tracing events for every agent invocation.
  - If a stage fails, marks status as FAILED and preserves partial trace for diagnostics.
"""

import json
import logging
from datetime import datetime
from typing import Optional, Union

from semantic_kernel.agents import SequentialOrchestration

from backend.config import settings
from backend.core.orchestration import create_kernel
from backend.core.schemas import (
    WorkflowState,
    SyllabusData,
    EvidenceRecord,
    CoverageEntry,
    GapRecord,
    Recommendation,
    ReviewResult,
    ReviewStatus,
)
from backend.core.shared_state import (
    create_workflow_state,
    update_state_status,
    add_error,
    validate_state_for_stage,
    state_to_json,
)
from backend.core.tracing import (
    trace_agent_start,
    trace_agent_end,
    trace_agent_error,
)
from backend.database.db import SessionLocal, init_database
from backend.database.models import (
    AnalysisRun,
    SyllabusDocument,
    RetrievedEvidence,
    RecommendationRecord,
)

# Import the 5 specialist agents
from backend.agents.syllabus_parser import SyllabusParserAgent
from backend.agents.skills_retriever import SkillsRetrieverAgent
from backend.agents.gap_detector import GapDetectorAgent
from backend.agents.resource_recommender import ResourceRecommenderAgent
from backend.agents.reviewer import ReviewerAgent

logger = logging.getLogger(__name__)


class CurriculumCoordinator:
    """
    Central Orchestrator managing pipeline execution, shared state transitions,
    execution tracing, and persistence.
    """

    def __init__(self):
        self.name = "CurriculumCoordinator"
        init_database()

        # Initialize Semantic Kernel
        self.kernel = create_kernel()

        # Initialize all 5 specialist agents with the shared Kernel
        self.parser_agent = SyllabusParserAgent(kernel=self.kernel)
        self.retriever_agent = SkillsRetrieverAgent(kernel=self.kernel)
        self.detector_agent = GapDetectorAgent(kernel=self.kernel)
        self.recommender_agent = ResourceRecommenderAgent(kernel=self.kernel)
        self.reviewer_agent = ReviewerAgent(kernel=self.kernel)

        # Register agents in Semantic Kernel SequentialOrchestration
        sk_agents = [
            self.parser_agent.sk_agent,
            self.retriever_agent.sk_agent,
            self.detector_agent.sk_agent,
            self.recommender_agent.sk_agent,
            self.reviewer_agent.sk_agent,
        ]
        self.orchestration = SequentialOrchestration(
            members=[a for a in sk_agents if a is not None],
            name="CurriculumGapAnalysisSequentialPipeline",
            description="Sequential multi-agent workflow analyzing academic syllabi against industry frameworks.",
        )

    def run_pipeline(
        self,
        domain: str,
        syllabus_input: Union[str, bytes],
        is_pdf: bool = True,
        filename: Optional[str] = None,
        run_id: Optional[str] = None,
        covered_threshold: Optional[float] = None,
        partial_threshold: Optional[float] = None,
    ) -> WorkflowState:
        """
        Executes the complete 6-stage sequential agent pipeline.

        Args:
            domain: Academic/industry domain (e.g. 'Data Science').
            syllabus_input: Raw text string or PDF file path / bytes.
            is_pdf: Whether input is PDF.
            filename: Original file name.
            run_id: Optional custom run ID.
            covered_threshold: Similarity cutoff for COVERED.
            partial_threshold: Similarity cutoff for PARTIAL.

        Returns:
            The complete, finalized WorkflowState object.
        """
        # 1. Initialize Shared State
        state = create_workflow_state(domain=domain, run_id=run_id)
        update_state_status(state, status="RUNNING", step=1, agent_name=self.parser_agent.name)

        db = SessionLocal()
        try:
            # Create persistent AnalysisRun record in DB
            db_run = AnalysisRun(
                id=state.run_id,
                domain=domain,
                status="RUNNING",
                mode=state.mode,
                created_at=state.created_at,
                shared_state_json=state_to_json(state),
            )
            db.add(db_run)
            db.commit()

            # -------------------------------------------------------------
            # STEP 1: Syllabus Parser Agent
            # -------------------------------------------------------------
            evt1_id = trace_agent_start(
                db=db,
                run_id=state.run_id,
                step_number=1,
                agent_name=self.parser_agent.name,
                input_summary=f"Parsing syllabus ({filename or 'raw text'})",
            )
            try:
                if is_pdf:
                    if isinstance(syllabus_input, bytes):
                        parsed_syl = self.parser_agent.parse_pdf_bytes(
                            syllabus_input, filename=filename or "upload.pdf"
                        )
                    else:
                        parsed_syl = self.parser_agent.parse_pdf_file(str(syllabus_input))
                else:
                    parsed_syl = self.parser_agent.parse_text(
                        str(syllabus_input),
                        filename=filename,
                        source_type="text",
                    )

                state.syllabus_data = parsed_syl
                trace_agent_end(
                    db=db,
                    event_id=evt1_id,
                    output_summary=f"Extracted {len(parsed_syl.all_topics)} topics across {len(parsed_syl.subjects)} subject(s).",
                )
            except Exception as e:
                trace_agent_error(db=db, event_id=evt1_id, error_details=str(e))
                add_error(state, f"Step 1 (Parser) failed: {e}")
                update_state_status(state, status="FAILED")
                self._persist_final_state(db, state)
                return state

            # -------------------------------------------------------------
            # STEP 2: Skills Framework Retrieval Agent (RAG)
            # -------------------------------------------------------------
            update_state_status(state, status="RUNNING", step=2, agent_name=self.retriever_agent.name)
            evt2_id = trace_agent_start(
                db=db,
                run_id=state.run_id,
                step_number=2,
                agent_name=self.retriever_agent.name,
                input_summary=f"Retrieving industry framework skills for domain '{domain}'",
            )
            try:
                evidence = self.retriever_agent.retrieve_evidence(
                    syllabus_data=state.syllabus_data,
                    domain=domain,
                )
                state.framework_evidence = evidence
                trace_agent_end(
                    db=db,
                    event_id=evt2_id,
                    output_summary=f"Retrieved {len(evidence)} verified framework evidence records.",
                    evidence_ids=[e.evidence_id for e in evidence[:10]],
                )
            except Exception as e:
                trace_agent_error(db=db, event_id=evt2_id, error_details=str(e))
                add_error(state, f"Step 2 (Retriever) failed: {e}")
                update_state_status(state, status="FAILED")
                self._persist_final_state(db, state)
                return state

            # -------------------------------------------------------------
            # STEP 3: Gap Detector Agent
            # -------------------------------------------------------------
            update_state_status(state, status="RUNNING", step=3, agent_name=self.detector_agent.name)
            evt3_id = trace_agent_start(
                db=db,
                run_id=state.run_id,
                step_number=3,
                agent_name=self.detector_agent.name,
                input_summary=f"Comparing {len(state.syllabus_data.all_topics)} topics with {len(state.framework_evidence)} evidence records",
            )
            try:
                matrix, gaps = self.detector_agent.detect_gaps(
                    syllabus_data=state.syllabus_data,
                    evidence_records=state.framework_evidence,
                    covered_threshold=covered_threshold,
                    partial_threshold=partial_threshold,
                )
                state.coverage_matrix = matrix
                state.gaps = gaps

                covered_cnt = sum(1 for c in matrix if c.status.value == "COVERED")
                partial_cnt = sum(1 for c in matrix if c.status.value == "PARTIAL")
                missing_cnt = sum(1 for c in matrix if c.status.value == "MISSING")

                trace_agent_end(
                    db=db,
                    event_id=evt3_id,
                    output_summary=f"Classified {len(matrix)} competencies: {covered_cnt} COVERED, {partial_cnt} PARTIAL, {missing_cnt} MISSING.",
                    evidence_ids=[g.evidence_id for g in gaps],
                )
            except Exception as e:
                trace_agent_error(db=db, event_id=evt3_id, error_details=str(e))
                add_error(state, f"Step 3 (Gap Detector) failed: {e}")
                update_state_status(state, status="FAILED")
                self._persist_final_state(db, state)
                return state

            # -------------------------------------------------------------
            # STEP 4: Resource Recommender Agent
            # -------------------------------------------------------------
            update_state_status(state, status="RUNNING", step=4, agent_name=self.recommender_agent.name)
            evt4_id = trace_agent_start(
                db=db,
                run_id=state.run_id,
                step_number=4,
                agent_name=self.recommender_agent.name,
                input_summary=f"Formulating recommendations for {len(state.gaps)} detected gaps",
            )
            try:
                recommendations = self.recommender_agent.recommend(
                    gaps=state.gaps,
                    evidence_records=state.framework_evidence,
                )
                state.recommendations = recommendations
                trace_agent_end(
                    db=db,
                    event_id=evt4_id,
                    output_summary=f"Generated {len(recommendations)} suggested curriculum additions with learning resources.",
                    evidence_ids=[r.evidence_id for r in recommendations],
                )
            except Exception as e:
                trace_agent_error(db=db, event_id=evt4_id, error_details=str(e))
                add_error(state, f"Step 4 (Recommender) failed: {e}")
                update_state_status(state, status="FAILED")
                self._persist_final_state(db, state)
                return state

            # -------------------------------------------------------------
            # STEP 5: Reviewer Agent (Validation)
            # -------------------------------------------------------------
            update_state_status(state, status="RUNNING", step=5, agent_name=self.reviewer_agent.name)
            evt5_id = trace_agent_start(
                db=db,
                run_id=state.run_id,
                step_number=5,
                agent_name=self.reviewer_agent.name,
                input_summary=f"Auditing {len(state.recommendations)} recommendations against evidence citations",
            )
            try:
                reviews = self.reviewer_agent.review(
                    recommendations=state.recommendations,
                    evidence_records=state.framework_evidence,
                )
                state.reviewer_results = reviews

                app_cnt = sum(1 for r in reviews if r.status == ReviewStatus.APPROVED)
                rej_cnt = sum(1 for r in reviews if r.status == ReviewStatus.REJECTED)

                trace_agent_end(
                    db=db,
                    event_id=evt5_id,
                    output_summary=f"Audit complete: {app_cnt} APPROVED, {rej_cnt} REJECTED.",
                    evidence_ids=[r.evidence_id for r in reviews],
                )
            except Exception as e:
                trace_agent_error(db=db, event_id=evt5_id, error_details=str(e))
                add_error(state, f"Step 5 (Reviewer) failed: {e}")
                update_state_status(state, status="FAILED")
                self._persist_final_state(db, state)
                return state

            # -------------------------------------------------------------
            # STEP 6: Coordinator Final Report Compilation
            # -------------------------------------------------------------
            update_state_status(state, status="RUNNING", step=6, agent_name=self.name)
            evt6_id = trace_agent_start(
                db=db,
                run_id=state.run_id,
                step_number=6,
                agent_name=self.name,
                input_summary="Synthesizing final report and persisting analysis results",
            )
            try:
                stats = state.statistics
                state.final_report = {
                    "run_id": state.run_id,
                    "domain": domain,
                    "mode": state.mode,
                    "generated_at": datetime.utcnow().isoformat(),
                    "statistics": stats,
                    "total_topics_analyzed": len(state.syllabus_data.all_topics),
                    "total_gaps": len(state.gaps),
                    "approved_recommendations": len(state.approved_recommendations),
                    "rejected_recommendations": len(state.rejected_recommendations),
                }

                trace_agent_end(
                    db=db,
                    event_id=evt6_id,
                    output_summary=f"Final analysis synthesized. Total Gaps: {len(state.gaps)}, Approved: {len(state.approved_recommendations)}.",
                )

                update_state_status(state, status="COMPLETED")
                self._persist_final_state(db, state)

            except Exception as e:
                trace_agent_error(db=db, event_id=evt6_id, error_details=str(e))
                add_error(state, f"Step 6 (Synthesis) failed: {e}")
                update_state_status(state, status="FAILED")
                self._persist_final_state(db, state)
                return state

        finally:
            db.close()

        logger.info(f"[{self.name}] Pipeline execution successfully finished for {state.run_id}")
        return state

    def _persist_final_state(self, db, state: WorkflowState) -> None:
        """Saves the complete workflow state and individual records into SQLite."""
        try:
            db_run = db.query(AnalysisRun).filter(AnalysisRun.id == state.run_id).first()
            if db_run:
                db_run.status = state.status
                db_run.completed_at = state.completed_at or datetime.utcnow()
                db_run.shared_state_json = state_to_json(state)

                # Persist recommendations with review status
                review_dict = {
                    r.recommendation_id: (r.status.value, r.reason)
                    for r in state.reviewer_results
                }
                for rec in state.recommendations:
                    status_val, reason_val = review_dict.get(
                        rec.recommendation_id, ("PENDING", "")
                    )
                    rec_record = RecommendationRecord(
                        id=rec.recommendation_id,
                        run_id=state.run_id,
                        topic=rec.topic,
                        reason=rec.reason,
                        recommended_weight=rec.recommended_weight,
                        level=rec.level,
                        resource_name=rec.resource,
                        resource_url=rec.resource_url,
                        framework_id=rec.framework_id,
                        evidence_id=rec.evidence_id,
                        review_status=status_val,
                        review_reason=reason_val,
                    )
                    db.merge(rec_record)

                db.commit()
                logger.info(f"[{self.name}] Saved persistent state for run {state.run_id}")
        except Exception as e:
            logger.error(f"[{self.name}] Failed to persist state for run {state.run_id}: {e}")
            db.rollback()
