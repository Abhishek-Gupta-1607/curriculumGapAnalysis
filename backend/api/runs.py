"""
backend/api/runs.py
===================
API endpoints for querying historical runs, real-time agent execution traces,
coverage matrices, and reviewer results.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.db import get_db
from backend.database.models import AnalysisRun
from backend.core.tracing import get_run_events
from backend.core.shared_state import state_from_json
from backend.core.schemas import RunSummary

router = APIRouter(prefix="/api/runs", tags=["Runs"])


@router.get("", response_model=list[RunSummary])
def list_runs(limit: int = 50, db: Session = Depends(get_db)):
    """
    Returns list of historical analysis runs.
    """
    # Auto-resolve any stale runs stuck in RUNNING from past crashed sessions
    cutoff = datetime.utcnow() - timedelta(minutes=2)
    stale_runs = (
        db.query(AnalysisRun)
        .filter(AnalysisRun.status == "RUNNING", AnalysisRun.created_at < cutoff)
        .all()
    )
    for sr in stale_runs:
        sr.status = "COMPLETED" if sr.shared_state_json else "FAILED"
    if stale_runs:
        db.commit()

    runs = (
        db.query(AnalysisRun)
        .order_by(AnalysisRun.created_at.desc())
        .limit(limit)
        .all()
    )

    summaries = []
    for r in runs:
        gaps_count = 0
        app_recs = 0
        if r.shared_state_json:
            try:
                st = state_from_json(r.shared_state_json)
                gaps_count = len(st.gaps)
                app_recs = len(st.approved_recommendations)
            except Exception:
                pass

        created_at_utc = r.created_at
        if created_at_utc and created_at_utc.tzinfo is None:
            created_at_utc = created_at_utc.replace(tzinfo=timezone.utc)

        completed_at_utc = r.completed_at
        if completed_at_utc and completed_at_utc.tzinfo is None:
            completed_at_utc = completed_at_utc.replace(tzinfo=timezone.utc)

        summaries.append(
            RunSummary(
                run_id=r.id,
                domain=r.domain,
                status=r.status,
                mode=r.mode,
                created_at=created_at_utc,
                completed_at=completed_at_utc,
                total_gaps=gaps_count,
                approved_recommendations=app_recs,
            )
        )
    return summaries


@router.get("/summary/stats")
def get_runs_stats(db: Session = Depends(get_db)):
    """
    Returns high-level aggregate statistics across all runs in the database.
    """
    # Auto-resolve any stale runs stuck in RUNNING from past crashed sessions
    cutoff = datetime.utcnow() - timedelta(minutes=2)
    stale_runs = (
        db.query(AnalysisRun)
        .filter(AnalysisRun.status == "RUNNING", AnalysisRun.created_at < cutoff)
        .all()
    )
    for sr in stale_runs:
        sr.status = "COMPLETED" if sr.shared_state_json else "FAILED"
    if stale_runs:
        db.commit()

    total_runs = db.query(AnalysisRun).count()
    completed_runs = db.query(AnalysisRun).filter(AnalysisRun.status == "COMPLETED").count()
    runs = db.query(AnalysisRun).all()
    total_gaps = 0
    total_recs = 0
    for r in runs:
        if r.shared_state_json:
            try:
                st = state_from_json(r.shared_state_json)
                total_gaps += len(st.gaps)
                total_recs += len(st.approved_recommendations)
            except Exception:
                pass
    return {
        "total_runs": total_runs,
        "completed_runs": completed_runs,
        "total_gaps": total_gaps,
        "total_approved_recommendations": total_recs,
    }


@router.get("/{run_id}")
def get_run_detail(run_id: str, db: Session = Depends(get_db)):
    """
    Returns complete WorkflowState data for a specific analysis run.
    """
    run_record = db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()
    if not run_record:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")

    if not run_record.shared_state_json:
        return {
            "run_id": run_record.id,
            "domain": run_record.domain,
            "status": run_record.status,
            "mode": run_record.mode,
        }

    st = state_from_json(run_record.shared_state_json)
    return st.model_dump()


@router.get("/{run_id}/events")
def get_run_agent_events(run_id: str, db: Session = Depends(get_db)):
    """
    Returns real agent execution trace records for the live agent monitor.
    """
    events = get_run_events(db, run_id)
    if not events:
        # Check if run exists
        run_record = db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()
        if not run_record:
            raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
    return events


@router.get("/{run_id}/gaps")
def get_run_gaps(run_id: str, db: Session = Depends(get_db)):
    """
    Returns coverage matrix and identified gaps for a run.
    """
    run_record = db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()
    if not run_record or not run_record.shared_state_json:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")

    st = state_from_json(run_record.shared_state_json)
    return {
        "run_id": run_id,
        "domain": st.domain,
        "coverage_matrix": [c.model_dump() for c in st.coverage_matrix],
        "gaps": [g.model_dump() for g in st.gaps],
        "statistics": st.statistics,
    }


@router.get("/{run_id}/recommendations")
def get_run_recommendations(run_id: str, db: Session = Depends(get_db)):
    """
    Returns approved and rejected curriculum recommendations for a run.
    """
    run_record = db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()
    if not run_record or not run_record.shared_state_json:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")

    st = state_from_json(run_record.shared_state_json)
    return {
        "run_id": run_id,
        "domain": st.domain,
        "approved": [r.model_dump() for r in st.approved_recommendations],
        "rejected": [r.model_dump() for r in st.rejected_recommendations],
        "all_recommendations": [r.model_dump() for r in st.recommendations],
        "reviewer_results": [r.model_dump() for r in st.reviewer_results],
    }
