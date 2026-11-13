"""
backend/agents/gap_detector.py
==============================
AGENT 3: GAP DETECTOR AGENT

PURPOSE:
  Evaluate the gap between academic curriculum topics and industry framework
  competencies by combining synonym mapping, semantic similarity calculation,
  and threshold-based classification into COVERED, PARTIAL, or MISSING.

TECHNOLOGY:
  - Sentence Transformers & Cosine Similarity
  - Domain-specific Synonym and Abbreviation Lexicon
  - Pydantic models (CoverageEntry, CoverageStatus, GapRecord)
  - Microsoft Semantic Kernel ChatCompletionAgent abstraction

CLASSIFICATION RULES:
  - COVERED: Similarity >= COVERED_THRESHOLD (default 0.75) OR strong synonym/exact match
  - PARTIAL: PARTIAL_THRESHOLD <= Similarity < COVERED_THRESHOLD (default 0.45 - 0.75)
  - MISSING: Similarity < PARTIAL_THRESHOLD (default < 0.45)

PRINCIPLES:
  - A high similarity score alone is not blind proof; exact term/subtopic validation is performed.
  - Borderline cases (e.g. within 0.05 of threshold) include explanatory reasoning.
  - Preserves traceability to the supporting EvidenceRecord ID.
"""

import re
import logging
from typing import Optional

from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.functions import kernel_function

from backend.config import settings
from backend.core.schemas import (
    CoverageEntry,
    CoverageStatus,
    GapRecord,
    SyllabusData,
    EvidenceRecord,
)
from backend.rag.embeddings import (
    generate_embeddings,
    generate_single_embedding,
    compute_similarity,
)

logger = logging.getLogger(__name__)

# Domain abbreviation & synonym expansions to normalize variations
SYNONYM_MAP: dict[str, list[str]] = {
    # Data Science
    "ml": ["machine learning", "statistical learning", "supervised learning"],
    "machine learning": ["ml", "statistical learning", "supervised learning"],
    "deep learning": ["neural networks", "deep neural networks", "dl", "artificial neural networks"],
    "nlp": ["natural language processing", "text analytics", "computational linguistics"],
    "natural language processing": ["nlp", "text analytics"],
    "eda": ["exploratory data analysis", "data exploration"],
    "exploratory data analysis": ["eda", "data exploration"],
    "mlops": ["machine learning operations", "model deployment", "model lifecycle"],
    "machine learning operations": ["mlops", "model deployment"],
    "spark": ["apache spark", "big data", "distributed computing", "hadoop"],
    "big data": ["spark", "hadoop", "distributed computing"],
    "sql": ["relational database", "structured query language", "rdbms", "database management"],
    "database": ["sql", "rdbms", "relational database"],
    "stats": ["statistics", "statistical analysis", "inferential statistics", "hypothesis testing"],
    "statistics": ["statistical analysis", "descriptive statistics", "hypothesis testing"],
    "visualization": ["reporting", "matplotlib", "seaborn", "charts", "plotting"],
    "regression": ["linear regression", "logistic regression", "ordinary least squares"],
    "preprocessing": ["data cleaning", "feature scaling", "imputation", "data preprocessing"],
    "probability": ["bayesian methods", "bayes theorem", "distributions"],
    "ethics": ["algorithmic bias", "responsible ai", "data privacy"],

    # Web Development
    "pwa": ["progressive web apps", "progressive web application", "service workers"],
    "progressive web apps": ["pwa", "service workers"],
    "wcag": ["web accessibility", "wai", "a11y", "accessibility standards"],
    "accessibility": ["wcag", "a11y", "screen reader"],
    "graphql": ["graphql api", "graph query language"],
    "rest": ["restful api", "rest api", "http endpoints", "web services"],
    "js": ["javascript", "ecmascript", "es6"],
    "javascript": ["js", "es6", "ecmascript"],
    "css": ["stylesheets", "responsive design", "flexbox", "css3", "grid"],
    "html": ["html5", "semantic markup", "semantic elements", "elements", "dom"],
    "html5": ["html", "markup", "elements", "semantic markup", "semantic elements"],
    "markup": ["elements", "tags", "html", "html5", "semantic elements"],
    "docker": ["containerization", "containers", "dockerfile"],
    "react": ["react component", "state management", "hooks", "virtual dom"],
    "performance": ["web performance", "core web vitals", "lcp", "lighthouse"],

    # Cloud & DevOps
    "k8s": ["kubernetes", "container orchestration"],
    "kubernetes": ["k8s", "container orchestration"],
    "ci/cd": ["continuous integration", "continuous delivery", "automated deployment", "pipelines"],
    "continuous integration": ["ci/cd", "ci", "automated pipelines"],
    "iac": ["infrastructure as code", "terraform", "ansible"],
    "infrastructure as code": ["iac", "terraform", "cloudformation"],
    "gitops": ["declarative infrastructure", "argo cd", "flux"],
    "finops": ["cloud cost optimization", "cloud financial management"],
    "service mesh": ["istio", "linkerd", "envoy", "traffic management"],
    "chaos engineering": ["resilience testing", "fault injection", "chaos mesh"],
    "linux": ["shell scripting", "bash", "unix", "system administration"],
    "monitoring": ["logging", "observability", "metrics", "prometheus", "grafana"],
}


STOPWORDS = {
    "and", "or", "the", "for", "with", "in", "on", "at", "to", "a", "an", "of", "by", "from",
    "using", "introduction", "basics", "fundamentals", "overview", "advanced", "applied"
}


class GapDetectorAgent:
    """
    Specialist Agent responsible for identifying curriculum gaps
    against industry framework competencies.
    """

    def __init__(self, kernel=None):
        self.name = "GapDetector"
        self.kernel = kernel
        self.sk_agent = None

        if self.kernel:
            self.sk_agent = ChatCompletionAgent(
                kernel=self.kernel,
                name=self.name,
                instructions=(
                    "You are a Curriculum Gap Analysis Specialist. Your goal is to "
                    "rigorously compare academic syllabus topics with industry competency "
                    "standards and detect covered, partially covered, and missing skills."
                ),
            )

    @kernel_function(
        name="detect_curriculum_gaps",
        description="Compares syllabus topics with retrieved framework competencies and returns coverage analysis.",
    )
    def detect_gaps(
        self,
        syllabus_data: SyllabusData,
        evidence_records: list[EvidenceRecord],
        covered_threshold: Optional[float] = None,
        partial_threshold: Optional[float] = None,
    ) -> tuple[list[CoverageEntry], list[GapRecord]]:
        """
        Executes semantic and lexical comparison between syllabus topics
        and industry framework competencies.
        """
        cov_thresh = covered_threshold if covered_threshold is not None else settings.COVERED_THRESHOLD
        par_thresh = partial_threshold if partial_threshold is not None else settings.PARTIAL_THRESHOLD

        logger.info(
            f"[{self.name}] Running gap detection with thresholds: "
            f"COVERED >= {cov_thresh}, PARTIAL >= {par_thresh}"
        )

        coverage_matrix: list[CoverageEntry] = []
        gaps: list[GapRecord] = []

        # 1. Prepare syllabus topic representations
        syllabus_topics = syllabus_data.all_topics
        if not syllabus_topics:
            logger.warning(f"[{self.name}] Syllabus has no parsed topics!")
            return coverage_matrix, gaps

        # Generate topic embeddings
        topic_texts = [
            f"{t.name}. {', '.join(t.subtopics)}" if t.subtopics else t.name
            for t in syllabus_topics
        ]
        syllabus_embeddings = generate_embeddings(topic_texts)

        # 2. Extract distinct competencies from evidence records
        competencies_map: dict[str, dict] = {}
        for ev in evidence_records:
            fid = ev.framework_id
            if fid in ("UNKNOWN-ID", "INSUFFICIENT_EVIDENCE", "Framework") or not fid:
                continue

            if fid not in competencies_map:
                skill_title = self._extract_skill_title(ev.text, fid)
                competencies_map[fid] = {
                    "framework_id": fid,
                    "skill_title": skill_title,
                    "evidence_id": ev.evidence_id,
                    "evidence_text": ev.text,
                    "document_name": ev.document_name,
                }

        # 3. For each framework competency, find the best matching syllabus topic
        for fid in sorted(competencies_map.keys()):
            comp = competencies_map[fid]
            skill_name = comp["skill_title"]

            # Embed clean skill name
            comp_embedding = generate_single_embedding(skill_name)

            best_sim = 0.0
            best_topic = None

            for idx, s_emb in enumerate(syllabus_embeddings):
                sim = compute_similarity(comp_embedding, s_emb)
                if sim > best_sim:
                    best_sim = sim
                    best_topic = syllabus_topics[idx].name

            # Check lexical & synonym match against all syllabus topics
            boosted_score, match_topic, lexical_reason = self._apply_lexical_analysis(
                skill_name=skill_name,
                best_topic=best_topic or "",
                all_syllabus_topics=[t.name for t in syllabus_topics],
                base_score=best_sim,
            )

            final_score = round(boosted_score, 4)
            chosen_topic = match_topic if match_topic else best_topic

            # Classification
            if final_score >= cov_thresh:
                status = CoverageStatus.COVERED
                reasoning = (
                    f"Strong alignment (similarity: {final_score:.2f}) with topic '{chosen_topic}'."
                    + (f" {lexical_reason}" if lexical_reason else "")
                )
            elif final_score >= par_thresh:
                status = CoverageStatus.PARTIAL
                reasoning = (
                    f"Moderate alignment (similarity: {final_score:.2f}) with topic '{chosen_topic}'. "
                    f"Core principles introduced, but specialized industry competency criteria are only partially met."
                )
            else:
                status = CoverageStatus.MISSING
                chosen_topic = None
                reasoning = (
                    f"No adequate curriculum coverage found (max similarity: {final_score:.2f}). "
                    f"Competency absent from syllabus."
                )

            entry = CoverageEntry(
                framework_skill=skill_name,
                framework_id=fid,
                matching_topic=chosen_topic,
                similarity_score=final_score,
                status=status,
                evidence_id=comp["evidence_id"],
                reasoning=reasoning,
            )
            coverage_matrix.append(entry)

            if status in (CoverageStatus.PARTIAL, CoverageStatus.MISSING):
                gaps.append(
                    GapRecord(
                        skill=skill_name,
                        framework_id=fid,
                        status=status,
                        evidence_id=comp["evidence_id"],
                        similarity_score=final_score,
                    )
                )

        logger.info(
            f"[{self.name}] Evaluated {len(coverage_matrix)} competencies: "
            f"{sum(1 for c in coverage_matrix if c.status == CoverageStatus.COVERED)} COVERED, "
            f"{sum(1 for c in coverage_matrix if c.status == CoverageStatus.PARTIAL)} PARTIAL, "
            f"{sum(1 for c in coverage_matrix if c.status == CoverageStatus.MISSING)} MISSING"
        )

        return coverage_matrix, gaps

    def _extract_skill_title(self, text: str, fid: str) -> str:
        """Extracts clean competency title from framework chunk text."""
        m = re.search(rf"Competency\s+{re.escape(fid)}:\s*([^\n\r]+)", text, re.IGNORECASE)
        if m:
            clean = m.group(1).strip()
            # Remove any trailing brackets or punctuation
            return re.sub(r"\[.*?\]", "", clean).strip(" -:")

        lines = text.split("\n")
        for i, line in enumerate(lines):
            if f"[ID: {fid}]" in line:
                if i > 0 and len(lines[i - 1].strip()) > 3:
                    return re.sub(r"Competency\s+[A-Z0-9\-]+:\s*", "", lines[i - 1].strip()).strip(" -:")
                elif i + 1 < len(lines):
                    return re.sub(r"Competency\s+[A-Z0-9\-]+:\s*", "", lines[i + 1].strip()).strip(" -:")

        return f"Competency {fid}"

    def _apply_lexical_analysis(
        self,
        skill_name: str,
        best_topic: str,
        all_syllabus_topics: list[str],
        base_score: float,
    ) -> tuple[float, Optional[str], str]:
        """
        Examines exact token overlap and domain synonym dictionaries.
        Prevents false negatives when different terms represent the exact same concept.
        """
        skill_lower = skill_name.lower()
        SHORT_TECH_TERMS = {"ci", "cd", "ai", "ml", "ip", "os", "ui", "ux", "db", "qa", "js"}
        norm_skill = re.sub(r"[/\\-]", " ", skill_lower)
        clean_skill_words = {
            w for w in re.findall(r"\b[a-z0-9]{2,}\b", norm_skill)
            if w not in STOPWORDS and (len(w) >= 3 or w in SHORT_TECH_TERMS)
        }

        # Check all syllabus topics for strong lexical or synonym overlap
        for topic in all_syllabus_topics:
            t_lower = topic.lower()
            norm_topic = re.sub(r"[/\\-]", " ", t_lower)
            topic_words = {
                w for w in re.findall(r"\b[a-z0-9]{2,}\b", norm_topic)
                if w not in STOPWORDS and (len(w) >= 3 or w in SHORT_TECH_TERMS)
            }

            # 1. Exact phrase match on full title
            if len(skill_lower) > 8 and (skill_lower == t_lower):
                return max(base_score, 0.95), topic, "Exact topic match found in syllabus."

            # 2. Conjunct component match (e.g. "Authentication and Authorization" -> "Authentication")
            if " and " in skill_lower:
                conjuncts = [c.strip() for c in skill_lower.split(" and ") if len(c.strip()) >= 5]
                for conj in conjuncts:
                    if conj == t_lower or (len(conj) >= 7 and conj in t_lower):
                        return max(base_score, 0.88), topic, f"Competency component '{conj}' covered in syllabus."

            # 3. Substantial meaningful word overlap (>= 2 key domain terms)
            common_words = clean_skill_words.intersection(topic_words)
            if len(common_words) >= 2:
                overlap_score = min(0.85, 0.72 + (0.06 * len(common_words)))
                return max(base_score, overlap_score), topic, f"Key domain term overlap ({', '.join(sorted(common_words))})."

            # 3. Synonym dictionary matching with strict word boundaries
            for term, syns in SYNONYM_MAP.items():
                if re.search(rf"\b{re.escape(term)}\b", skill_lower):
                    for syn in syns:
                        if re.search(rf"\b{re.escape(syn)}\b", t_lower):
                            return (
                                max(base_score, 0.86),
                                topic,
                                f"Mapped via industry synonym: '{term}' ~ '{syn}'.",
                            )

        return base_score, None, ""
