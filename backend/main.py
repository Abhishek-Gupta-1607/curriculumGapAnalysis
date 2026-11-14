"""
backend/main.py
===============
FastAPI Main Application Entry Point.

WHAT THIS FILE DOES:
  1. Creates FastAPI application with OpenAPI documentation.
  2. Sets up CORS middleware to allow React frontend (localhost:5173).
  3. Initializes SQLite database tables on startup.
  4. Mounts static storage directories for reports and uploads.
  5. Registers all /api routes from backend/api/routes.py.
  6. Pre-flight check for virtual environment packages.

TO RUN:
  uvicorn backend.main:app --reload --port 8000
"""

import sys
from pathlib import Path

# Verify virtual environment packages
try:
    import semantic_kernel
except ModuleNotFoundError:
    print("\n" + "=" * 75)
    print("ENVIRONMENT ERROR: 'semantic_kernel' was not found.")
    print("Please activate your virtual environment before running the server:")
    print("  source venv/bin/activate")
    print("  uvicorn backend.main:app --reload --port 8000")
    print("=" * 75 + "\n")
    sys.exit(1)

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import settings, PROJECT_ROOT
from backend.database.db import init_database
from backend.api.routes import api_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("backend.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events: initialize database and verify folders on startup.
    """
    logger.info("Initializing Curriculum Gap Analysis Backend...")
    init_database()

    # Ensure storage directories exist
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.REPORTS_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.CHROMA_PERSIST_DIR).mkdir(parents=True, exist_ok=True)

    logger.info(f"System operating in mode: {settings.mode_label}")
    yield
    logger.info("Shutting down backend server.")


app = FastAPI(
    title="Curriculum Gap Analysis Pipeline API",
    description=(
        "Evidence-Based Multi-Agent AI System analyzing academic syllabi against "
        "industry competency standards (NIST NICE, ESCO, ACM) using Semantic Kernel and local RAG."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration for React frontend
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(api_router)


@app.get("/")
def root():
    return {
        "system": "Curriculum Gap Analysis Pipeline",
        "status": "online",
        "mode": settings.mode_label,
        "docs_url": "/docs",
        "api_health": "/api/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=True,
    )
