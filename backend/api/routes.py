"""
backend/api/routes.py
=====================
Root router aggregating all sub-routes, health checks, and sample syllabus downloads.
"""

from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import FileResponse

from backend.config import settings, PROJECT_ROOT
from backend.core.schemas import HealthResponse
from backend.api.analysis import router as analysis_router
from backend.api.runs import router as runs_router
from backend.api.reports import router as reports_router

api_router = APIRouter()

# Include sub-routers
api_router.include_router(analysis_router)
api_router.include_router(runs_router)
api_router.include_router(reports_router)


@api_router.get("/health", response_model=HealthResponse, tags=["System"])
@api_router.get("/api/health", response_model=HealthResponse, tags=["System"])
def health_check():
    """
    Health check endpoint returning system status and operating mode.
    """
    return HealthResponse(
        status="healthy",
        mode=settings.mode_label,
        version="1.0.0",
        database="connected",
    )


@api_router.get("/samples", tags=["System"])
@api_router.get("/api/samples", tags=["System"])
def list_sample_syllabi():
    """
    Returns list of built-in sample syllabi available for demonstration.
    """
    samples = [
        {
            "domain": "Data Science",
            "title": "BSc Data Science - Semester 5 Syllabus",
            "filename": "data_science.pdf",
            "download_url": "/api/samples/data_science.pdf",
            "known_gaps": ["MLOps", "Big Data (Spark)", "Deep Learning", "NLP", "Data Ethics"],
        },
        {
            "domain": "Web Development",
            "title": "BSc IT - Web Development Specialization Syllabus",
            "filename": "web_development.pdf",
            "download_url": "/api/samples/web_development.pdf",
            "known_gaps": ["Web Accessibility (WCAG)", "Progressive Web Apps (PWA)", "GraphQL", "Docker Containers", "Core Web Vitals"],
        },
        {
            "domain": "Cloud and DevOps",
            "title": "BSc CS - Cloud Computing and DevOps Syllabus",
            "filename": "cloud_devops.pdf",
            "download_url": "/api/samples/cloud_devops.pdf",
            "known_gaps": ["Kubernetes", "Service Mesh (Istio)", "Chaos Engineering", "GitOps", "FinOps / Cost Optimization"],
        },
    ]
    return samples


@api_router.get("/samples/{filename}", tags=["System"])
def get_sample_file(filename: str):
    """
    Downloads or previews a sample syllabus PDF.
    """
    path = PROJECT_ROOT / "data" / "syllabi" / filename
    if not path.exists():
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Sample '{filename}' not found.")
    return FileResponse(
        path=str(path),
        media_type="application/pdf",
        filename=filename,
    )
