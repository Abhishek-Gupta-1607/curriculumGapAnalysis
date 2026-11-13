"""
tests/test_coordinator.py
=========================
Integration tests for Agent 6: Curriculum Coordinator.

Verifies:
  - Full sequential pipeline execution end-to-end.
  - Verification of state isolation across independent runs.
  - Error handling when provided invalid or empty inputs.
"""

import pytest
from backend.agents.curriculum_coordinator import CurriculumCoordinator
from backend.core.schemas import WorkflowState


class TestCurriculumCoordinator:
    def test_run_pipeline_end_to_end(self):
        """Pipeline should execute all 6 stages sequentially for Data Science."""
        coordinator = CurriculumCoordinator()
        state = coordinator.run_pipeline(
            domain="Data Science",
            syllabus_input="data/syllabi/data_science.pdf",
            is_pdf=True,
            filename="data_science.pdf",
        )

        assert isinstance(state, WorkflowState)
        assert state.status == "COMPLETED"
        assert state.current_step == 6
        assert state.syllabus_data is not None
        assert len(state.syllabus_data.all_topics) > 0
        assert len(state.framework_evidence) > 0
        assert len(state.coverage_matrix) > 0
        assert len(state.gaps) > 0
        assert len(state.approved_recommendations) > 0
        assert len(state.reviewer_results) > 0

    def test_run_pipeline_state_isolation(self):
        """Two runs must have distinct run_ids and independent state objects."""
        coordinator = CurriculumCoordinator()
        state1 = coordinator.run_pipeline(
            domain="Web Development",
            syllabus_input="data/syllabi/web_development.pdf",
            is_pdf=True,
            filename="web_development.pdf",
        )
        state2 = coordinator.run_pipeline(
            domain="Cloud and DevOps",
            syllabus_input="data/syllabi/cloud_devops.pdf",
            is_pdf=True,
            filename="cloud_devops.pdf",
        )

        assert state1.run_id != state2.run_id
        assert state1.domain == "Web Development"
        assert state2.domain == "Cloud and DevOps"
        assert state1.status == "COMPLETED"
        assert state2.status == "COMPLETED"

    def test_run_pipeline_empty_text_graceful_handling(self):
        """Coordinator should handle empty text input gracefully without crashing."""
        coordinator = CurriculumCoordinator()
        state = coordinator.run_pipeline(
            domain="Data Science",
            syllabus_input="",
            is_pdf=False,
            filename="empty.txt",
        )

        # Empty text still completes with empty topics or handled status
        assert state.status in ("COMPLETED", "FAILED")
