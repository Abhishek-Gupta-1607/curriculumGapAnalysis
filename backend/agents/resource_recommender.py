"""
backend/agents/resource_recommender.py
======================================
AGENT 4: RESOURCE RECOMMENDER AGENT

PURPOSE:
  Generate evidence-backed curriculum recommendations for competencies
  identified as MISSING or PARTIALLY covered in the gap detection stage.

TECHNOLOGY:
  - Curated verified resource catalog (data/resources/learning_resources.json)
  - Retrieved framework evidence records
  - Pydantic Recommendation models
  - Microsoft Semantic Kernel ChatCompletionAgent abstraction

RESPONSIBILITIES:
  1. For every confirmed gap (PARTIAL or MISSING), formulate a concrete curriculum addition.
  2. Propose a clearly labeled "Suggested" academic weight (never claimed as official).
  3. Attach learning level (Beginner, Intermediate, Advanced).
  4. Attach verified open learning resources and documentation URLs.
  5. Bind each recommendation to its exact supporting evidence_id and framework_id.
"""

import json
import logging
from pathlib import Path
from typing import Optional

from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.functions import kernel_function

from backend.config import settings
from backend.core.schemas import GapRecord, Recommendation, EvidenceRecord

logger = logging.getLogger(__name__)


class ResourceRecommenderAgent:
    """
    Specialist Agent responsible for generating actionable, evidence-linked
    curriculum addition proposals and learning resources.
    """

    def __init__(self, kernel=None):
        self.name = "ResourceRecommender"
        self.kernel = kernel
        self.sk_agent = None
        self._catalog = self._load_catalog()

        if self.kernel:
            self.sk_agent = ChatCompletionAgent(
                kernel=self.kernel,
                name=self.name,
                instructions=(
                    "You are a Curriculum Remediation Specialist. Your role is to "
                    "propose structured topic additions and verified open educational "
                    "resources for detected curriculum gaps, strictly citing framework evidence."
                ),
            )

    def _load_catalog(self) -> dict:
        """Loads curated learning resources catalog from disk."""
        catalog_path = Path(settings.RESOURCES_FILE)
        if catalog_path.exists():
            try:
                with open(catalog_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("resources", {})
            except Exception as e:
                logger.error(f"[{self.name}] Failed to load resource catalog: {e}")
        return {}

    @kernel_function(
        name="recommend_resources",
        description="Produces actionable curriculum recommendations with learning resources for detected gaps.",
    )
    def recommend(
        self,
        gaps: list[GapRecord],
        evidence_records: list[EvidenceRecord],
    ) -> list[Recommendation]:
        """
        Generates structured recommendations for all identified curriculum gaps.
        """
        logger.info(f"[{self.name}] Generating recommendations for {len(gaps)} gaps")
        recommendations: list[Recommendation] = []

        # Build evidence lookup by framework_id
        ev_map: dict[str, EvidenceRecord] = {}
        for ev in evidence_records:
            if ev.framework_id not in ev_map:
                ev_map[ev.framework_id] = ev

        for gap in gaps:
            fid = gap.framework_id
            ev = ev_map.get(fid)
            evidence_id = ev.evidence_id if ev else gap.evidence_id

            # Consult curated catalog for verified resources
            cat_entry = self._catalog.get(fid)

            if cat_entry:
                topic_title = cat_entry.get("topic", gap.skill)
                reason = cat_entry.get(
                    "reason",
                    f"Required industry competency '{gap.skill}' identified in framework."
                )
                rec_weight = cat_entry.get("recommended_weight", 8.0)
                level = cat_entry.get("level", "Intermediate")

                items = cat_entry.get("items", [])
                resource_name = items[0]["name"] if items else "Industry Framework Specification"
                resource_url = items[0]["url"] if items else (ev.source_url if ev else "")
            else:
                # Fallback to evidence record text
                topic_title = gap.skill
                reason = (
                    f"Directly derived from {ev.document_name if ev else 'Industry Framework'}: "
                    f"This competency is required for professional industry readiness."
                )
                rec_weight = 8.0
                level = "Intermediate"
                resource_name = f"{ev.document_name if ev else 'Framework'} Guidelines"
                resource_url = ev.source_url if ev else ""

            rec = Recommendation(
                topic=topic_title,
                reason=reason,
                recommended_weight=rec_weight,
                weight_type="Suggested",
                level=level,
                resource=resource_name,
                resource_url=resource_url,
                framework_id=fid,
                evidence_id=evidence_id,
            )
            recommendations.append(rec)

        logger.info(
            f"[{self.name}] Generated {len(recommendations)} recommendations backed by evidence"
        )
        return recommendations
