"""
backend/core/tracing.py
========================
Agent execution tracing — records what each agent did.

WHAT THIS FILE DOES:
  - Creates trace events when an agent starts and finishes.
  - Measures execution time in milliseconds.
  - Stores trace events in the database.
  - Provides an API to retrieve events for a run.

WHY DO WE NEED THIS?
  - Proves the agents actually ran (not simulated).
  - Debugging: if something fails, we see exactly which step broke.
  - The frontend Agent Monitor page displays these real events.
  - Viva demonstration: show real execution records.

HOW IT WORKS:
  1. Before an agent runs → call trace_agent_start()
  2. After it completes  → call trace_agent_end()
  3. If it fails          → call trace_agent_error()
  Each call creates/updates an AgentEvent row in SQLite.
"""

import uuid
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from backend.database.models import AgentEvent

logger = logging.getLogger(__name__)


def _generate_event_id() -> str:
    """Create a short unique event ID."""
    return f"EVT-{uuid.uuid4().hex[:8].upper()}"


def trace_agent_start(
    db: Session,
    run_id: str,
    step_number: int,
    agent_name: str,
    input_summary: str = "",
) -> str:
    """
    Record that an agent has started execution.

    Args:
        db: Database session.
        run_id: The analysis run ID.
        step_number: Pipeline step (1-6).
        agent_name: Name of the agent (e.g. "SyllabusParser").
        input_summary: Brief description of what the agent received.

    Returns:
        The event_id for this trace (needed by trace_agent_end).
    """
    event_id = _generate_event_id()

    event = AgentEvent(
        id=event_id,
        run_id=run_id,
        step_number=step_number,
        agent_name=agent_name,
        status="STARTED",
        started_at=datetime.utcnow(),
        input_summary=input_summary[:500] if input_summary else "",
        token_usage=0,
    )

    db.add(event)
    db.commit()

    logger.info(f"[{run_id}] Step {step_number}: {agent_name} STARTED")
    return event_id


def trace_agent_end(
    db: Session,
    event_id: str,
    output_summary: str = "",
    evidence_ids: Optional[list[str]] = None,
    token_usage: int = 0,
) -> None:
    """
    Record that an agent has completed successfully.

    Args:
        db: Database session.
        event_id: The event ID from trace_agent_start().
        output_summary: Brief description of what the agent produced.
        evidence_ids: List of evidence IDs the agent worked with.
        token_usage: Number of LLM tokens used (0 if offline).
    """
    event = db.query(AgentEvent).filter(AgentEvent.id == event_id).first()

    if event is None:
        logger.error(f"Trace event {event_id} not found — cannot record end")
        return

    now = datetime.utcnow()
    event.status = "COMPLETED"
    event.finished_at = now
    event.output_summary = output_summary[:500] if output_summary else ""
    event.evidence_ids = evidence_ids or []
    event.token_usage = token_usage

    # Calculate duration in milliseconds
    if event.started_at:
        delta = now - event.started_at
        event.duration_ms = int(delta.total_seconds() * 1000)

    db.commit()

    logger.info(
        f"[{event.run_id}] Step {event.step_number}: "
        f"{event.agent_name} COMPLETED ({event.duration_ms}ms)"
    )


def trace_agent_error(
    db: Session,
    event_id: str,
    error_details: str,
) -> None:
    """
    Record that an agent has failed.

    Args:
        db: Database session.
        event_id: The event ID from trace_agent_start().
        error_details: Description of what went wrong.
    """
    event = db.query(AgentEvent).filter(AgentEvent.id == event_id).first()

    if event is None:
        logger.error(f"Trace event {event_id} not found — cannot record error")
        return

    now = datetime.utcnow()
    event.status = "FAILED"
    event.finished_at = now
    event.error_details = error_details[:1000] if error_details else ""

    if event.started_at:
        delta = now - event.started_at
        event.duration_ms = int(delta.total_seconds() * 1000)

    db.commit()

    logger.error(
        f"[{event.run_id}] Step {event.step_number}: "
        f"{event.agent_name} FAILED — {error_details[:200]}"
    )


def get_run_events(db: Session, run_id: str) -> list[dict]:
    """
    Retrieve all agent events for a specific run, ordered by step.

    Returns a list of dictionaries (ready for API response).
    """
    events = (
        db.query(AgentEvent)
        .filter(AgentEvent.run_id == run_id)
        .order_by(AgentEvent.step_number)
        .all()
    )

    return [
        {
            "event_id": e.id,
            "run_id": e.run_id,
            "step_number": e.step_number,
            "agent_name": e.agent_name,
            "status": e.status,
            "started_at": e.started_at.isoformat() if e.started_at else None,
            "finished_at": e.finished_at.isoformat() if e.finished_at else None,
            "duration_ms": e.duration_ms,
            "input_summary": e.input_summary,
            "output_summary": e.output_summary,
            "token_usage": e.token_usage,
            "error_details": e.error_details,
            "evidence_ids": e.evidence_ids or [],
        }
        for e in events
    ]
