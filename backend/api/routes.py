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
    Returns list of built-in sample syllabi available for demonstration across all domains.
    """
    samples = [
        {
            "domain": "Data Science",
            "title": "BSc Data Science & Analytics Curriculum",
            "filename": "data_science.txt",
            "download_url": "/api/samples/data_science.pdf",
            "known_gaps": ["MLOps", "Big Data Pipelines", "AI Ethics", "Vector Databases", "Deep RL"],
        },
        {
            "domain": "Web Development",
            "title": "Web Engineering & Modern Frontend Curriculum",
            "filename": "web_development.txt",
            "download_url": "/api/samples/web_development.pdf",
            "known_gaps": ["WCAG Accessibility", "Core Web Vitals", "PWA", "OWASP Security", "E2E Testing"],
        },
        {
            "domain": "Cloud and DevOps",
            "title": "Cloud Computing & Site Reliability Curriculum",
            "filename": "cloud_devops.txt",
            "download_url": "/api/samples/cloud_devops.pdf",
            "known_gaps": ["Terraform IaC", "Kubernetes Orchestration", "CI/CD Automation", "Distributed Tracing", "DevSecOps"],
        },
        {
            "domain": "Agentic AI",
            "title": "Autonomous Agent Systems & Multi-Agent AI Curriculum",
            "filename": "agentic_ai.txt",
            "download_url": "/api/samples/agentic_ai.pdf",
            "known_gaps": ["Multi-Agent Consensus", "Sandboxed Execution", "Model Context Protocol", "Agentic Benchmarks", "Prompt Injection Defense"],
        },
        {
            "domain": "Cybersecurity",
            "title": "Cybersecurity Defense & Ethical Hacking Curriculum",
            "filename": "cybersecurity.txt",
            "download_url": "/api/samples/cybersecurity.pdf",
            "known_gaps": ["Zero Trust Architecture", "DevSecOps Pipeline Scanning", "MITRE ATT&CK Framework", "OAuth 2.0 Security", "AI Threat Detection"],
        },
        {
            "domain": "Machine Learning",
            "title": "Applied Machine Learning & AI Engineering Curriculum",
            "filename": "machine_learning.txt",
            "download_url": "/api/samples/machine_learning.pdf",
            "known_gaps": ["MLOps (MLflow)", "Feature Stores", "Explainable AI (SHAP)", "Data Drift Detection", "Triton Inference Serving"],
        },
        {
            "domain": "Deep Learning",
            "title": "Deep Learning & Neural Architectures Curriculum",
            "filename": "deep_learning.txt",
            "download_url": "/api/samples/deep_learning.pdf",
            "known_gaps": ["LLM Fine-Tuning (LoRA)", "Diffusion Models", "Contrastive Vision (CLIP)", "TensorRT Quantization", "RLHF Alignment"],
        },
        {
            "domain": "Full Stack",
            "title": "Full Stack Web & Distributed Systems Curriculum",
            "filename": "full_stack.txt",
            "download_url": "/api/samples/full_stack.pdf",
            "known_gaps": ["Next.js App Router (SSR)", "WebSockets Real-Time", "Redis Caching", "GraphQL & Apollo", "Dockerized CI/CD"],
        },
    ]
    return samples


@api_router.get("/samples/{filename}", tags=["System"])
@api_router.get("/api/samples/{filename}", tags=["System"])
def get_sample_file(filename: str):
    """
    Downloads or previews a sample syllabus (PDF or TXT content).
    """
    path = PROJECT_ROOT / "data" / "syllabi" / filename
    if not path.exists():
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Sample '{filename}' not found.")
    
    if filename.endswith(".txt"):
        text = path.read_text(encoding="utf-8")
        return {"filename": filename, "content": text}

    return FileResponse(
        path=str(path),
        media_type="application/pdf",
        filename=filename,
    )
