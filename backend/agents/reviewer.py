"""
backend/agents/reviewer.py
==========================
AGENT 5: REVIEWER AGENT (MANDATORY VALIDATION MODULE)

PURPOSE:
  Provide strict, deterministic verification of every proposed curriculum
  recommendation against actual persisted framework evidence before recommendations
  are admitted into the final report.

TECHNOLOGY:
  - Python deterministic rule-based auditing
  - Pydantic models (ReviewResult, ReviewStatus, Recommendation)
  - Microsoft Semantic Kernel ChatCompletionAgent abstraction

VERIFICATION PROTOCOL:
  Each recommendation must pass ALL of the following criteria:
  1. Evidence Existence Check:
     - evidence_id must exist in the shared retrieved framework evidence store.
  2. Framework ID Consistency Check:
     - The recommendation's framework_id must match the retrieved evidence's framework_id.
  3. Source Document Authenticity Check:
     - The referenced evidence must contain document_name and verified source metadata.
  4. Granular Page/Section Citation Check:
     - The referenced evidence must specify a valid page number or section header.
  5. Learning Resource Integrity Check:
     - The resource_url must be non-empty and start with a valid HTTP/HTTPS protocol.

OUTPUT:
  - List of ReviewResult objects detailing APPROVED or REJECTED status,
    specific reasons, and checks passed/failed.
  - Guarantees zero unverified citations appear in approved reports.
"""

import logging
from typing import Optional

from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.functions import kernel_function

from backend.core.schemas import (
    Recommendation,
    ReviewResult,
    ReviewStatus,
    EvidenceRecord,
)

logger = logging.getLogger(__name__)


class ReviewerAgent:
    """
    Specialist Auditor Agent responsible for defending report integrity
    through deterministic citation verification.
    """

    def __init__(self, kernel=None):
        self.name = "Reviewer"
        self.kernel = kernel
        self.sk_agent = None

        if self.kernel:
            self.sk_agent = ChatCompletionAgent(
                kernel=self.kernel,
                name=self.name,
                instructions=(
                    "You are a Rigorous Academic & Industry Alignment Auditor. "
                    "Your mandate is to verify that all proposed curriculum additions "
                    "are strictly backed by genuine framework evidence citations and "
                    "reject any recommendation lacking authentic verifiable backing."
                ),
            )

    @kernel_function(
        name="review_recommendations",
        description="Audits recommendations against stored evidence records and returns approval/rejection decisions.",
    )
    def review(
        self,
        recommendations: list[Recommendation],
        evidence_records: list[EvidenceRecord],
    ) -> list[ReviewResult]:
        """
        Deterministically audits each recommendation against the retrieved evidence list.
        """
        logger.info(
            f"[{self.name}] Auditing {len(recommendations)} recommendations "
            f"against {len(evidence_records)} evidence records"
        )
        results: list[ReviewResult] = []

        # Build fast lookup table of genuine evidence records
        evidence_lookup: dict[str, EvidenceRecord] = {
            ev.evidence_id: ev for ev in evidence_records
        }

        for rec in recommendations:
            passed_checks: list[str] = []
            failed_checks: list[str] = []

            # ---------------------------------------------------------
            # Check 1: Evidence Existence
            # ---------------------------------------------------------
            ev = evidence_lookup.get(rec.evidence_id)
            if ev is not None:
                passed_checks.append(f"Evidence record '{rec.evidence_id}' exists in shared state.")
            else:
                failed_checks.append(f"Evidence ID '{rec.evidence_id}' does not exist in retrieved evidence store.")

            # ---------------------------------------------------------
            # Check 2: Framework ID Consistency
            # ---------------------------------------------------------
            if ev and ev.framework_id == rec.framework_id:
                passed_checks.append(f"Framework ID '{rec.framework_id}' matches supporting evidence.")
            elif ev:
                failed_checks.append(
                    f"Framework ID mismatch: recommendation specifies '{rec.framework_id}' "
                    f"but evidence record '{rec.evidence_id}' references '{ev.framework_id}'."
                )

            # ---------------------------------------------------------
            # Check 3: Source Document Authenticity
            # ---------------------------------------------------------
            if ev and ev.document_name and ev.document_name.strip() and ev.document_name != "N/A":
                passed_checks.append(f"Document attribution verified: '{ev.document_name}'.")
            elif ev:
                failed_checks.append("Evidence record lacks authentic document metadata.")

            # ---------------------------------------------------------
            # Check 4: Page / Section Citation Metadata
            # ---------------------------------------------------------
            if ev and (ev.page is not None or (ev.section and ev.section.strip())):
                loc_desc = f"page {ev.page}" if ev.page is not None else f"section '{ev.section}'"
                passed_checks.append(f"Citation location verified: {loc_desc}.")
            elif ev:
                failed_checks.append("Evidence record lacks page or section citation location.")

            # ---------------------------------------------------------
            # Check 5: Resource URL Integrity
            # ---------------------------------------------------------
            if rec.resource_url and (
                rec.resource_url.startswith("http://") or rec.resource_url.startswith("https://")
            ):
                passed_checks.append(f"Learning resource URL verified: {rec.resource_url}.")
            else:
                failed_checks.append(f"Missing or malformed learning resource URL: '{rec.resource_url}'.")

            # ---------------------------------------------------------
            # Final Decision
            # ---------------------------------------------------------
            if not failed_checks:
                status = ReviewStatus.APPROVED
                reason = "Valid retrieved framework evidence with verified citations."
            else:
                status = ReviewStatus.REJECTED
                reason = "; ".join(failed_checks)

            review_res = ReviewResult(
                recommendation_id=rec.recommendation_id,
                topic=rec.topic,
                evidence_id=rec.evidence_id,
                status=status,
                reason=reason,
                checks_passed=passed_checks,
                checks_failed=failed_checks,
            )
            results.append(review_res)

        approved_count = sum(1 for r in results if r.status == ReviewStatus.APPROVED)
        rejected_count = sum(1 for r in results if r.status == ReviewStatus.REJECTED)

        logger.info(
            f"[{self.name}] Audit complete: {approved_count} APPROVED, {rejected_count} REJECTED"
        )
        return results
