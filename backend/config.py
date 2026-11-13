"""
backend/config.py
=================
Central configuration for the Curriculum Gap Analysis Pipeline.

Loads settings from environment variables (via .env file).
Every setting has a sensible default so the app works out of the box
in offline mode without any .env file.

HOW IT WORKS:
  1. python-dotenv reads the .env file in the project root.
  2. os.getenv() reads each variable with a fallback default.
  3. The Settings dataclass groups all config in one importable object.

USAGE:
  from backend.config import settings
  print(settings.LLM_ENABLED)        # False
  print(settings.EMBEDDING_MODEL)     # "all-MiniLM-L6-v2"
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from dotenv import load_dotenv

# ── Find the project root (the folder containing 'backend/') ──
# This works whether you run from the project root or from backend/
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ── Load .env file if it exists ──
dotenv_path = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path)


def _get_bool(key: str, default: str = "false") -> bool:
    """Read an env var as a boolean. 'true'/'1'/'yes' → True."""
    return os.getenv(key, default).lower() in ("true", "1", "yes")


def _get_float(key: str, default: str) -> float:
    """Read an env var as a float."""
    return float(os.getenv(key, default))


def _get_int(key: str, default: str) -> int:
    """Read an env var as an integer."""
    return int(os.getenv(key, default))


@dataclass
class Settings:
    """
    All application settings in one place.

    Attributes are grouped by purpose. Each one maps to an
    environment variable with the same name (see .env.example).
    """

    # ── LLM Configuration ──
    LLM_ENABLED: bool = field(default_factory=lambda: _get_bool("LLM_ENABLED"))
    LLM_PROVIDER: str = field(default_factory=lambda: os.getenv("LLM_PROVIDER", ""))
    LLM_MODEL: str = field(default_factory=lambda: os.getenv("LLM_MODEL", ""))
    LLM_API_KEY: str = field(default_factory=lambda: os.getenv("LLM_API_KEY", ""))

    # ── Embedding Model ──
    EMBEDDING_MODEL: str = field(
        default_factory=lambda: os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    )

    # ── Gap Detection Thresholds ──
    COVERED_THRESHOLD: float = field(
        default_factory=lambda: _get_float("COVERED_THRESHOLD", "0.75")
    )
    PARTIAL_THRESHOLD: float = field(
        default_factory=lambda: _get_float("PARTIAL_THRESHOLD", "0.45")
    )

    # ── RAG Settings ──
    RAG_TOP_K: int = field(default_factory=lambda: _get_int("RAG_TOP_K", "5"))
    RAG_CHUNK_SIZE: int = field(
        default_factory=lambda: _get_int("RAG_CHUNK_SIZE", "500")
    )
    RAG_CHUNK_OVERLAP: int = field(
        default_factory=lambda: _get_int("RAG_CHUNK_OVERLAP", "50")
    )

    # ── Database ──
    DATABASE_URL: str = field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL",
            f"sqlite:///{PROJECT_ROOT / 'storage' / 'app.db'}",
        )
    )

    # ── ChromaDB ──
    CHROMA_PERSIST_DIR: str = field(
        default_factory=lambda: os.getenv(
            "CHROMA_PERSIST_DIR",
            str(PROJECT_ROOT / "storage" / "chroma_db"),
        )
    )

    # ── File Storage ──
    UPLOAD_DIR: str = field(
        default_factory=lambda: os.getenv(
            "UPLOAD_DIR", str(PROJECT_ROOT / "storage" / "uploads")
        )
    )
    REPORTS_DIR: str = field(
        default_factory=lambda: os.getenv(
            "REPORTS_DIR", str(PROJECT_ROOT / "storage" / "reports")
        )
    )

    # ── Server ──
    BACKEND_HOST: str = field(
        default_factory=lambda: os.getenv("BACKEND_HOST", "0.0.0.0")
    )
    BACKEND_PORT: int = field(
        default_factory=lambda: _get_int("BACKEND_PORT", "8000")
    )
    FRONTEND_URL: str = field(
        default_factory=lambda: os.getenv("FRONTEND_URL", "http://localhost:5173")
    )

    # ── Upload Limits ──
    MAX_UPLOAD_SIZE_MB: int = field(
        default_factory=lambda: _get_int("MAX_UPLOAD_SIZE_MB", "10")
    )

    # ── Derived Paths (computed from PROJECT_ROOT) ──
    SYLLABI_DIR: str = field(
        default_factory=lambda: str(PROJECT_ROOT / "data" / "syllabi")
    )
    FRAMEWORKS_DIR: str = field(
        default_factory=lambda: str(PROJECT_ROOT / "data" / "frameworks")
    )
    RESOURCES_FILE: str = field(
        default_factory=lambda: str(
            PROJECT_ROOT / "data" / "resources" / "learning_resources.json"
        )
    )
    GROUND_TRUTH_FILE: str = field(
        default_factory=lambda: str(PROJECT_ROOT / "evaluation" / "ground_truth.json")
    )

    @property
    def mode_label(self) -> str:
        """Human-readable label for the current operating mode."""
        return "LLM-ASSISTED" if self.LLM_ENABLED else "OFFLINE"


# ── Create a single global settings instance ──
# Import this everywhere:  from backend.config import settings
settings = Settings()
