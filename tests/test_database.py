"""
tests/test_database.py
======================
Tests for database setup and ORM models.
"""

import os
import pytest
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database.db import Base
from backend.database.models import (
    AnalysisRun,
    AgentEvent,
    SyllabusDocument,
    FrameworkDocument,
)


@pytest.fixture
def test_db():
    """
    Create an in-memory SQLite database for testing.

    This fixture:
    1. Creates a fresh in-memory database.
    2. Creates all tables.
    3. Provides a session for the test.
    4. Cleans up after the test.

    Using in-memory DB means tests don't affect the real database.
    """
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


class TestAnalysisRun:
    def test_create_run(self, test_db):
        """Should create and retrieve an analysis run."""
        run = AnalysisRun(
            id="RUN-TEST-001",
            domain="Data Science",
            status="PENDING",
            mode="OFFLINE",
        )
        test_db.add(run)
        test_db.commit()

        fetched = test_db.query(AnalysisRun).filter_by(id="RUN-TEST-001").first()
        assert fetched is not None
        assert fetched.domain == "Data Science"
        assert fetched.status == "PENDING"

    def test_update_status(self, test_db):
        """Should update run status."""
        run = AnalysisRun(
            id="RUN-TEST-002",
            domain="Web Dev",
            status="PENDING",
        )
        test_db.add(run)
        test_db.commit()

        run.status = "COMPLETED"
        run.completed_at = datetime.utcnow()
        test_db.commit()

        fetched = test_db.query(AnalysisRun).filter_by(id="RUN-TEST-002").first()
        assert fetched.status == "COMPLETED"
        assert fetched.completed_at is not None


class TestAgentEvent:
    def test_create_event(self, test_db):
        """Should create agent trace events linked to a run."""
        # First create the parent run
        run = AnalysisRun(id="RUN-EVT-001", domain="Test")
        test_db.add(run)
        test_db.commit()

        # Then create the event
        event = AgentEvent(
            id="EVT-001",
            run_id="RUN-EVT-001",
            step_number=1,
            agent_name="SyllabusParser",
            status="COMPLETED",
            started_at=datetime.utcnow(),
            duration_ms=1500,
            input_summary="PDF with 5 pages",
            output_summary="Extracted 12 topics",
        )
        test_db.add(event)
        test_db.commit()

        fetched = test_db.query(AgentEvent).filter_by(id="EVT-001").first()
        assert fetched.agent_name == "SyllabusParser"
        assert fetched.duration_ms == 1500

    def test_run_has_events(self, test_db):
        """Run's events relationship should work."""
        run = AnalysisRun(id="RUN-EVT-002", domain="Test")
        test_db.add(run)
        test_db.commit()

        for i in range(3):
            event = AgentEvent(
                id=f"EVT-{i}",
                run_id="RUN-EVT-002",
                step_number=i + 1,
                agent_name=f"Agent{i+1}",
                status="COMPLETED",
            )
            test_db.add(event)
        test_db.commit()

        fetched_run = test_db.query(AnalysisRun).filter_by(id="RUN-EVT-002").first()
        assert len(fetched_run.events) == 3


class TestFrameworkDocument:
    def test_create_framework(self, test_db):
        """Should create a framework document record."""
        doc = FrameworkDocument(
            id="NICE-SP800-181",
            name="NIST SP 800-181 Rev 1",
            publisher="NIST",
            version="Rev 1",
            source_url="https://csrc.nist.gov/...",
            license="Public Domain",
            domain="Cybersecurity",
            chunk_count=0,
            ingestion_status="PENDING",
        )
        test_db.add(doc)
        test_db.commit()

        fetched = test_db.query(FrameworkDocument).filter_by(id="NICE-SP800-181").first()
        assert fetched.publisher == "NIST"
        assert fetched.license == "Public Domain"


class TestStateIsolationInDb:
    def test_different_runs_isolated(self, test_db):
        """Different runs should have independent data in the database."""
        run1 = AnalysisRun(id="RUN-ISO-A", domain="Domain A", status="COMPLETED")
        run2 = AnalysisRun(id="RUN-ISO-B", domain="Domain B", status="FAILED")
        test_db.add_all([run1, run2])
        test_db.commit()

        # Query each independently
        r1 = test_db.query(AnalysisRun).filter_by(id="RUN-ISO-A").first()
        r2 = test_db.query(AnalysisRun).filter_by(id="RUN-ISO-B").first()

        assert r1.domain == "Domain A"
        assert r1.status == "COMPLETED"
        assert r2.domain == "Domain B"
        assert r2.status == "FAILED"
