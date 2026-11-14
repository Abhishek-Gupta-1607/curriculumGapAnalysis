"""
backend/api/analysis.py
=======================
API endpoints for starting and monitoring syllabus gap analyses.
"""

import os
import shutil
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session

from backend.config import settings, PROJECT_ROOT
from backend.core.schemas import AnalyzeRequest, AnalyzeResponse
from backend.database.db import get_db
from backend.database.models import AnalysisRun
from backend.agents.curriculum_coordinator import CurriculumCoordinator
from backend.services.report_service import generate_json_report, generate_pdf_report

router = APIRouter(prefix="/api/analyze", tags=["Analysis"])


@router.post("", response_model=AnalyzeResponse)
def analyze_text(
    payload: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Initiates analysis on raw pasted syllabus text.
    """
    if not payload.syllabus_text or not payload.syllabus_text.strip():
        raise HTTPException(status_code=400, detail="Syllabus text cannot be empty.")

    coordinator = CurriculumCoordinator()

    # Execute coordinator pipeline
    state = coordinator.run_pipeline(
        domain=payload.domain,
        syllabus_input=payload.syllabus_text,
        is_pdf=False,
        filename=None,
        covered_threshold=payload.covered_threshold,
        partial_threshold=payload.partial_threshold,
    )

    # Generate reports asynchronously
    background_tasks.add_task(generate_json_report, state)
    background_tasks.add_task(generate_pdf_report, state)

    return AnalyzeResponse(
        run_id=state.run_id,
        status=state.status,
        message="Analysis completed successfully.",
    )


@router.post("/upload", response_model=AnalyzeResponse)
async def analyze_upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    domain: str = Form("Data Science"),
    covered_threshold: Optional[float] = Form(None),
    partial_threshold: Optional[float] = Form(None),
    db: Session = Depends(get_db),
):
    """
    Initiates analysis on an uploaded PDF syllabus document.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF syllabus documents are supported.")

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded PDF file is empty.")

    # Save to storage/uploads
    uploads_dir = Path(settings.UPLOAD_DIR)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    saved_file_path = uploads_dir / file.filename
    with open(saved_file_path, "wb") as f:
        f.write(content)

    coordinator = CurriculumCoordinator()

    state = coordinator.run_pipeline(
        domain=domain,
        syllabus_input=content,
        is_pdf=True,
        filename=file.filename,
        covered_threshold=covered_threshold,
        partial_threshold=partial_threshold,
    )

    background_tasks.add_task(generate_json_report, state)
    background_tasks.add_task(generate_pdf_report, state)

    return AnalyzeResponse(
        run_id=state.run_id,
        status=state.status,
        message=f"Analysis of '{file.filename}' completed successfully.",
    )
