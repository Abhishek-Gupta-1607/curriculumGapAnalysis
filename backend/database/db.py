"""
backend/database/db.py
======================
Database engine and session setup using SQLAlchemy.

WHAT THIS FILE DOES:
  - Creates a SQLAlchemy engine connected to SQLite.
  - Provides a session factory for database operations.
  - Creates all tables on first startup.

WHY SQLALCHEMY?
  - ORM (Object-Relational Mapper): lets us work with Python objects
    instead of writing raw SQL.
  - Database-agnostic: switching from SQLite to PostgreSQL later
    only requires changing the DATABASE_URL.
  - Built-in connection pooling and transaction management.

WHY SQLITE?
  - No server installation needed.
  - Single file (storage/app.db).
  - Perfect for local development and demos.
  - Can be replaced with PostgreSQL for production.
"""

import logging
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from backend.config import settings

logger = logging.getLogger(__name__)


# ── Base class for all ORM models ──
# Every database table model in models.py will inherit from this.
class Base(DeclarativeBase):
    pass


def _get_engine():
    """
    Create the SQLAlchemy engine.

    For SQLite:
      - check_same_thread=False: allows FastAPI (multi-threaded) to use SQLite.
      - WAL journal mode: better concurrent read performance.
    """
    # Ensure the storage directory exists
    if settings.DATABASE_URL.startswith("sqlite"):
        db_path = settings.DATABASE_URL.replace("sqlite:///", "")
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    engine = create_engine(
        settings.DATABASE_URL,
        # SQLite needs this for multi-threaded access (FastAPI uses threads)
        connect_args={"check_same_thread": False}
        if "sqlite" in settings.DATABASE_URL
        else {},
        # Echo SQL statements in debug mode (set to True for debugging)
        echo=False,
    )

    # Enable WAL mode for SQLite (better concurrent reads)
    if "sqlite" in settings.DATABASE_URL:
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


# ── Create engine and session factory ──
engine = _get_engine()

# SessionLocal is a factory: calling SessionLocal() creates a new session.
# autocommit=False: we control when to commit.
# autoflush=False: we control when to flush to DB.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_database():
    """
    Create all database tables.

    Call this once at application startup.
    SQLAlchemy checks which tables exist and only creates missing ones.
    """
    # Import models so SQLAlchemy knows about them
    from backend.database import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")


def get_db():
    """
    Database session dependency for FastAPI.

    Usage in FastAPI routes:
        @app.get("/example")
        def example(db: Session = Depends(get_db)):
            ...

    The session is automatically closed after the request finishes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
