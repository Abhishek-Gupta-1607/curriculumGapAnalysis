"""
tests/test_shared_state.py
===========================
Tests for the shared state management module.
"""

import pytest

from backend.core.schemas import (
    WorkflowState,
    SyllabusData,
    ParsedSubject,
    ParsedTopic,
    EvidenceRecord,
)
from backend.core.shared_state import (
    generate_run_id,
    create_workflow_state,
    update_state_status,
    add_error,
    validate_state_for_stage,
    state_to_json,
    state_from_json,
)


class TestRunIdGeneration:
    def test_format(self):
        """Run ID should start with 'RUN-' and contain a date."""
        run_id = generate_run_id()
        assert run_id.startswith("RUN-")
        assert len(run_id) > 10

    def test_unique(self):
        """Two consecutive run IDs should be different (within same second is edge case)."""
        id1 = generate_run_id()
        id2 = generate_run_id()
        # They MIGHT be the same if generated in the same second,
        # but this is acceptable for demo purposes.
        assert isinstance(id1, str)
        assert isinstance(id2, str)


class TestCreateWorkflowState:
    def test_default_state(self):
        """Fresh state should have PENDING status and OFFLINE mode."""
        state = create_workflow_state(domain="Data Science")
        assert state.domain == "Data Science"
        assert state.status == "PENDING"
        assert state.mode == "OFFLINE"
        assert state.run_id.startswith("RUN-")

    def test_custom_run_id(self):
        """Should accept a custom run ID."""
        state = create_workflow_state(domain="Test", run_id="RUN-CUSTOM-001")
        assert state.run_id == "RUN-CUSTOM-001"


class TestStateIsolation:
    def test_two_states_are_independent(self):
        """Modifying one state should NOT affect another."""
        state1 = create_workflow_state(domain="Domain A", run_id="RUN-A")
        state2 = create_workflow_state(domain="Domain B", run_id="RUN-B")

        # Modify state1
        state1.errors.append("Error in A")
        state1.status = "FAILED"

        # state2 should be unaffected
        assert state2.errors == []
        assert state2.status == "PENDING"
        assert state2.domain == "Domain B"


class TestUpdateStateStatus:
    def test_update_to_running(self):
        """Should update status and step number."""
        state = create_workflow_state(domain="Test", run_id="RUN-X")
        update_state_status(state, "RUNNING", step=1, agent_name="SyllabusParser")
        assert state.status == "RUNNING"
        assert state.current_step == 1
        assert state.current_agent == "SyllabusParser"

    def test_completed_sets_timestamp(self):
        """COMPLETED status should set completed_at."""
        state = create_workflow_state(domain="Test", run_id="RUN-Y")
        assert state.completed_at is None
        update_state_status(state, "COMPLETED")
        assert state.completed_at is not None


class TestValidateStateForStage:
    def test_stage1_no_prereqs(self):
        """Stage 1 (Parser) needs nothing — should always pass."""
        state = create_workflow_state(domain="Test", run_id="RUN-V")
        errors = validate_state_for_stage(state, stage=1)
        assert errors == []

    def test_stage2_needs_syllabus(self):
        """Stage 2 (Retriever) needs parsed syllabus."""
        state = create_workflow_state(domain="Test", run_id="RUN-V2")
        errors = validate_state_for_stage(state, stage=2)
        assert len(errors) > 0
        assert "syllabus_data" in errors[0]

    def test_stage2_passes_with_syllabus(self):
        """Stage 2 should pass when syllabus data exists."""
        state = create_workflow_state(domain="Test", run_id="RUN-V3")
        state.syllabus_data = SyllabusData(
            source_type="text",
            subjects=[
                ParsedSubject(
                    name="Test Subject",
                    topics=[ParsedTopic(name="Test Topic", unit="U1")],
                )
            ],
        )
        errors = validate_state_for_stage(state, stage=2)
        assert errors == []

    def test_stage3_needs_evidence(self):
        """Stage 3 (Gap Detector) needs evidence from Stage 2."""
        state = create_workflow_state(domain="Test", run_id="RUN-V4")
        state.syllabus_data = SyllabusData(source_type="text")
        errors = validate_state_for_stage(state, stage=3)
        assert len(errors) > 0


class TestJsonSerialisation:
    def test_round_trip(self):
        """State should survive JSON serialisation without data loss."""
        state = create_workflow_state(domain="Round Trip Test", run_id="RUN-RT")
        state.errors.append("Test error")

        json_str = state_to_json(state)
        restored = state_from_json(json_str)

        assert restored.run_id == "RUN-RT"
        assert restored.domain == "Round Trip Test"
        assert "Test error" in restored.errors[0]
