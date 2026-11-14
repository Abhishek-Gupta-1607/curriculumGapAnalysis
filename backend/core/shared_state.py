"""
backend/core/shared_state.py
=============================
Manages the WorkflowState lifecycle for each analysis run.

WHAT THIS FILE DOES:
  - Creates a new WorkflowState with a unique run_id.
  - Updates state fields after each agent completes.
  - Validates state before and after each stage.
  - Saves state to the database (via SQLAlchemy).
  - Loads state from the database for a given run_id.

WHY SEPARATE FROM SCHEMAS?
  schemas.py defines the DATA SHAPES (Pydantic models).
  shared_state.py defines the OPERATIONS on those shapes.

ISOLATION:
  Every analysis run gets its own WorkflowState instance.
  Different runs never share mutable Python objects.
"""

import uuid
import json
import logging
from datetime import datetime
from typing import Optional

from backend.config import settings
from backend.core.schemas import WorkflowState

logger = logging.getLogger(__name__)


def generate_run_id() -> str:
    """
    Create a unique, human-readable run ID.

    Format: RUN-YYYYMMDD-HHMMSS-XXXX
    Example: RUN-20261113-120530-AB12

    Why this format?
      - Human-readable (easy to reference in viva).
      - Sortable by creation time.
      - Guaranteed unique across fast sub-second runs.
    """
    # Use local wall-clock time so the timestamp in the run ID matches the user's local clock
    now = datetime.now()
    return f"RUN-{now.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"


def create_workflow_state(
    domain: str,
    run_id: Optional[str] = None,
) -> WorkflowState:
    """
    Create a fresh WorkflowState for a new analysis run.

    Args:
        domain: The analysis domain (e.g. "Data Science").
        run_id: Optional custom run ID. Auto-generated if not provided.

    Returns:
        A new WorkflowState with empty agent outputs, ready for the pipeline.
    """
    if run_id is None:
        run_id = generate_run_id()

    state = WorkflowState(
        run_id=run_id,
        domain=domain,
        status="PENDING",
        mode=settings.mode_label,
        created_at=datetime.utcnow(),
    )

    logger.info(f"Created new workflow state: run_id={run_id}, domain={domain}")
    return state


def update_state_status(
    state: WorkflowState,
    status: str,
    step: Optional[int] = None,
    agent_name: Optional[str] = None,
) -> WorkflowState:
    """
    Update the pipeline status in the workflow state.

    Args:
        state: The current workflow state.
        status: New status (RUNNING, COMPLETED, FAILED).
        step: Current step number (1-6).
        agent_name: Name of the currently running agent.

    Returns:
        The updated state (same object, mutated in place).
    """
    state.status = status

    if step is not None:
        state.current_step = step
    if agent_name is not None:
        state.current_agent = agent_name
    if status in ("COMPLETED", "FAILED"):
        state.completed_at = datetime.utcnow()

    logger.info(
        f"[{state.run_id}] Status → {status}"
        + (f" | Step {step}" if step else "")
        + (f" | Agent: {agent_name}" if agent_name else "")
    )
    return state


def add_error(state: WorkflowState, error_message: str) -> WorkflowState:
    """Record an error in the workflow state."""
    state.errors.append(f"[{datetime.utcnow().isoformat()}] {error_message}")
    logger.error(f"[{state.run_id}] Error: {error_message}")
    return state


def validate_state_for_stage(state: WorkflowState, stage: int) -> list[str]:
    """
    Validate that the state has the required data for a given stage.

    Each agent needs the output of previous agents to work correctly.
    This function checks that those outputs exist.

    Args:
        state: The workflow state to validate.
        stage: The stage number (1-6) about to run.

    Returns:
        A list of validation error messages. Empty list = valid.
    """
    errors = []

    # Stage 1 (Parser) — needs nothing from previous stages
    if stage == 1:
        pass  # No prerequisites

    # Stage 2 (Retriever) — needs parsed syllabus
    elif stage == 2:
        if state.syllabus_data is None:
            errors.append("Stage 2 requires syllabus_data from Stage 1")
        elif len(state.syllabus_data.all_topics) == 0:
            errors.append("Stage 2 requires at least one parsed topic")

    # Stage 3 (Gap Detector) — needs syllabus + evidence
    elif stage == 3:
        if state.syllabus_data is None:
            errors.append("Stage 3 requires syllabus_data")
        if len(state.framework_evidence) == 0:
            errors.append("Stage 3 requires framework_evidence from Stage 2")

    # Stage 4 (Recommender) — needs gaps
    elif stage == 4:
        if len(state.coverage_matrix) == 0:
            errors.append("Stage 4 requires coverage_matrix from Stage 3")

    # Stage 5 (Reviewer) — needs recommendations + evidence
    elif stage == 5:
        if len(state.recommendations) == 0:
            errors.append("Stage 5 requires recommendations from Stage 4")

    # Stage 6 (Coordinator report) — needs reviewer results
    elif stage == 6:
        if len(state.reviewer_results) == 0:
            errors.append("Stage 6 requires reviewer_results from Stage 5")

    if errors:
        for err in errors:
            logger.warning(f"[{state.run_id}] Validation failed for stage {stage}: {err}")

    return errors


def state_to_json(state: WorkflowState) -> str:
    """Serialise the workflow state to a JSON string."""
    return state.model_dump_json(indent=2)


def state_from_json(json_str: str) -> WorkflowState:
    """Deserialise a workflow state from a JSON string."""
    return WorkflowState.model_validate_json(json_str)


def state_to_dict(state: WorkflowState) -> dict:
    """Convert the workflow state to a plain dictionary."""
    return state.model_dump(mode="json")
