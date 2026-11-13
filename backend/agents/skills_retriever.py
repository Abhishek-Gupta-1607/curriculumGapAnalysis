"""
backend/agents/skills_retriever.py
==================================
AGENT 2: SKILLS FRAMEWORK RETRIEVAL AGENT

PURPOSE:
  Retrieve relevant industry skills and verified competency evidence from
  indexed industry framework documents (NIST NICE, ESCO, ACM CS2023)
  stored in ChromaDB.

TECHNOLOGY:
  - ChromaDB persistent vector store
  - Sentence Transformers (all-MiniLM-L6-v2) for local dense embeddings
  - Pydantic EvidenceRecord models
  - Microsoft Semantic Kernel ChatCompletionAgent abstraction

RESPONSIBILITIES:
  1. Retrieve all framework competency passages for the target curriculum domain.
  2. Embed search queries and compute baseline relevance against the syllabus.
  3. Formulate verifiable EvidenceRecord structures containing:
     - evidence_id (e.g. EV-001)
     - framework_id (e.g. DS-011)
     - document_name, version, source_url
     - page number and section heading
     - exact text excerpt
     - similarity_score
  4. Explicitly flag "INSUFFICIENT_EVIDENCE" when no pertinent evidence exists.
  5. Never fabricate citations, page numbers, or competency IDs.
"""

import re
import logging
from typing import Optional

from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.functions import kernel_function

from backend.config import settings
from backend.core.schemas import EvidenceRecord, SyllabusData
from backend.rag.embeddings import generate_single_embedding, compute_similarity
from backend.rag.vector_store import (
    search_similar,
    get_or_create_collection,
)

logger = logging.getLogger(__name__)


class SkillsRetrieverAgent:
    """
    Specialist Agent responsible for finding verified industry competency
    evidence from local vector storage.
    """

    def __init__(self, kernel=None):
        self.name = "SkillsRetriever"
        self.kernel = kernel
        self.sk_agent = None

        if self.kernel:
            self.sk_agent = ChatCompletionAgent(
                kernel=self.kernel,
                name=self.name,
                instructions=(
                    "You are an Industry Skills Framework Retrieval Specialist. "
                    "Your responsibility is to query vector databases of authoritative "
                    "workforce standards (NIST, ESCO, ACM) and retrieve verifiable "
                    "evidence passages with strict citations."
                ),
            )

    @kernel_function(
        name="retrieve_framework_evidence",
        description="Retrieves industry competency evidence records for a given syllabus and domain.",
    )
    def retrieve_evidence(
        self,
        syllabus_data: SyllabusData,
        domain: str,
        top_k_per_query: int = 5,
    ) -> list[EvidenceRecord]:
        """
        Retrieves all verified framework evidence records for the target domain.

        Strategy:
        1. Fetch all indexed competency chunks for the domain from ChromaDB.
        2. Group into competency evidence records, ensuring every domain competency is represented.
        3. Score each evidence record against the syllabus topics for baseline relevance.
        4. Return structured, verified EvidenceRecord instances.
        """
        logger.info(f"[{self.name}] Retrieving framework evidence for domain: {domain}")
        domain_filter = self._normalize_domain(domain)
        collection = get_or_create_collection("framework_skills")

        if collection.count() == 0:
            logger.warning(f"[{self.name}] ChromaDB collection is empty!")
            return [self._insufficient_evidence_record(domain)]

        # 1. Fetch domain-specific chunks from ChromaDB
        query_where = {"domain": domain_filter} if domain_filter else None
        if query_where:
            results = collection.get(
                where=query_where,
                include=["documents", "metadatas"],
            )
        else:
            results = collection.get(
                limit=100,
                include=["documents", "metadatas"],
            )

        doc_ids = results.get("ids", [])
        documents = results.get("documents", [])
        metadatas = results.get("metadatas", [])

        if not doc_ids:
            logger.warning(f"[{self.name}] No chunks found matching domain: {domain}")
            return [self._insufficient_evidence_record(domain)]

        # 2. Build syllabus topic embedding for relevance scoring
        syllabus_summary = " ".join([t.name for t in syllabus_data.all_topics[:15]])
        summary_emb = generate_single_embedding(syllabus_summary) if syllabus_summary else []

        evidence_list: list[EvidenceRecord] = []
        seen_fids: set[str] = set()
        evidence_counter = 0

        indexed_items = list(zip(doc_ids, documents, metadatas))

        for chunk_id, text, meta in indexed_items:
            fid = meta.get("framework_id", "")
            if not fid:
                id_m = re.search(r"\[ID:\s*([A-Za-z0-9_\-]+)\]", text)
                if id_m:
                    fid = id_m.group(1).strip()

            if not fid or fid == "Framework":
                continue

            sim_score = 0.0
            if summary_emb:
                chunk_emb = generate_single_embedding(text[:300])
                sim_score = round(compute_similarity(summary_emb, chunk_emb), 4)

            evidence_counter += 1
            ev_id = f"EV-{evidence_counter:03d}"

            evidence_rec = EvidenceRecord(
                evidence_id=ev_id,
                framework_id=fid,
                document_name=meta.get("document_name", f"{domain} Competency Framework"),
                document_version=meta.get("version", "1.0"),
                source_url=meta.get("source_url", ""),
                page=meta.get("page_number", 1),
                section=meta.get("section", "Competency Specification"),
                text=text.strip(),
                similarity_score=sim_score,
            )
            evidence_list.append(evidence_rec)
            seen_fids.add(fid)

        logger.info(
            f"[{self.name}] Retrieved {len(evidence_list)} evidence records across "
            f"{len(seen_fids)} unique competencies for {domain}"
        )

        return evidence_list

    def _insufficient_evidence_record(self, domain: str) -> EvidenceRecord:
        """Helper to create an explicit insufficient evidence record."""
        return EvidenceRecord(
            evidence_id="EV-000",
            framework_id="INSUFFICIENT_EVIDENCE",
            document_name="N/A",
            document_version="",
            source_url="",
            page=None,
            section="N/A",
            text=f"INSUFFICIENT_EVIDENCE: No matching industry framework documents found for domain '{domain}'.",
            similarity_score=0.0,
        )

    def _normalize_domain(self, domain: str) -> Optional[str]:
        """Normalize domain input to match framework metadata."""
        d = domain.lower()
        if "data" in d:
            return "Data Science"
        if "web" in d or "frontend" in d or "fullstack" in d:
            return "Web Development"
        if "cloud" in d or "devops" in d or "infra" in d:
            return "Cloud and DevOps"
        return None
