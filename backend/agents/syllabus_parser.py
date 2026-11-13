"""
backend/agents/syllabus_parser.py
=================================
AGENT 1: SYLLABUS PARSER AGENT

PURPOSE:
  Extract structured academic curriculum information (subjects, units,
  topics, subtopics, and official weights/marks) from raw syllabus text
  or syllabus PDF documents.

TECHNOLOGY:
  - Python regex patterns for unit/topic parsing
  - PyMuPDF text stream integration
  - Pydantic models (SyllabusData, ParsedSubject, ParsedTopic)
  - Microsoft Semantic Kernel ChatCompletionAgent abstraction

DESIGN PRINCIPLES:
  - Pure deterministic extraction in offline mode (no API key required).
  - Preserves exact extracted topic names without hallucination.
  - If official weights/hours are absent, marks them as None (never invents weights).
  - Flags unparseable or ambiguous sections in 'warnings'.
"""

import re
import logging
from typing import Optional

from pydantic import BaseModel, Field
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.functions import kernel_function

from backend.core.schemas import SyllabusData, ParsedSubject, ParsedTopic
from backend.services.pdf_service import extract_text_from_pdf, extract_text_from_bytes

logger = logging.getLogger(__name__)


class SyllabusParserAgent:
    """
    Specialist Agent responsible for converting raw syllabus inputs into
    structured academic curriculum models.
    """

    def __init__(self, kernel=None):
        self.name = "SyllabusParser"
        self.kernel = kernel
        self.sk_agent = None

        if self.kernel:
            self.sk_agent = ChatCompletionAgent(
                kernel=self.kernel,
                name=self.name,
                instructions=(
                    "You are a Senior Academic Curriculum Specialist. Your role is "
                    "to parse educational syllabi, identify core subjects, units, "
                    "topics, subtopics, and official marks or hours without inventing data."
                ),
            )

    @kernel_function(
        name="parse_syllabus_text",
        description="Parses raw syllabus text into structured SyllabusData.",
    )
    def parse_text(
        self,
        text: str,
        filename: Optional[str] = None,
        source_type: str = "text",
    ) -> SyllabusData:
        """
        Deterministic parser for syllabus text.

        Extracts:
        - Course / Programme title
        - Subjects
        - Units / Modules with topic lists and optional weights
        """
        if not text or not text.strip():
            return SyllabusData(
                source_type=source_type,
                filename=filename,
                course_name="Unknown Course",
                subjects=[],
                warnings=["Provided syllabus text was empty."],
            )

        lines = [line.strip() for line in text.split("\n") if line.strip()]
        warnings = []

        # 1. Detect Course Name (usually in the first 3 lines)
        course_name = "General Academic Curriculum"
        for line in lines[:5]:
            if any(term in line.lower() for term in ["syllabus", "curriculum", "course", "bachelor", "master", "bsc", "b.tech", "msc"]):
                course_name = line
                break

        # 2. Extract Units and Topics
        # Pattern examples:
        # Unit 1: Data Preprocessing (15 Hours / 20 Marks)
        # Module 2 - Supervised Learning
        # Topic 3.1: Linear Regression
        subjects_dict: dict[str, list[ParsedTopic]] = {}
        current_subject = course_name
        current_unit = "General Topics"

        # Regex patterns
        unit_pattern = re.compile(
            r"^(?:Unit|Module|Section|Part)\s*([0-9IVXLCDM]+)[\s:\-\.]*(.*)",
            re.IGNORECASE,
        )
        weight_pattern = re.compile(
            r"(?:(\d+(?:\.\d+)?)\s*(?:%|percent|marks|hrs|hours|credits|weight))",
            re.IGNORECASE,
        )

        current_topics: list[ParsedTopic] = []

        for line in lines:
            # Check for Unit/Module headers
            unit_match = unit_pattern.match(line)
            if unit_match:
                unit_num = unit_match.group(1)
                unit_title = unit_match.group(2).strip()
                current_unit = f"Unit {unit_num}"
                if unit_title:
                    current_unit += f": {unit_title}"

                # Check if unit header contains marks/weight
                w_match = weight_pattern.search(line)
                unit_weight = float(w_match.group(1)) if w_match else None

                # Create a topic placeholder for the unit itself if title exists
                if unit_title:
                    # Clean title of weight text
                    clean_title = weight_pattern.sub("", unit_title).strip(" -:()")
                    if clean_title:
                        current_topics.append(
                            ParsedTopic(
                                name=clean_title,
                                unit=f"Unit {unit_num}",
                                subtopics=[],
                                official_weight=unit_weight,
                            )
                        )
                continue

            # Check for bullet points or numbered subtopics
            bullet_match = re.match(r"^(?:[\*\-\•\d+\.]|\([a-z0-9]+\))\s*(.*)", line)
            if bullet_match:
                topic_text = bullet_match.group(1).strip()
                if not topic_text:
                    continue

                w_match = weight_pattern.search(topic_text)
                topic_weight = float(w_match.group(1)) if w_match else None
                clean_topic = weight_pattern.sub("", topic_text).strip(" -:()")
                # Strip leading numbering like .1, 1.2, 3), etc.
                clean_topic = re.sub(r"^[\.\d\s\-\*\•\)]+", "", clean_topic).strip()

                # Split subtopics by comma or semicolon if present
                subtopics = []
                if ":" in clean_topic:
                    parts = clean_topic.split(":", 1)
                    topic_name = parts[0].strip()
                    subtopics = [s.strip() for s in re.split(r"[,;]", parts[1]) if s.strip()]
                elif "," in clean_topic and len(clean_topic.split(",")) > 2:
                    parts = clean_topic.split(",")
                    topic_name = parts[0].strip()
                    subtopics = [s.strip() for s in parts[1:] if s.strip()]
                else:
                    topic_name = clean_topic

                if topic_name and len(topic_name) > 2:
                    current_topics.append(
                        ParsedTopic(
                            name=topic_name,
                            unit=current_unit,
                            subtopics=subtopics,
                            official_weight=topic_weight,
                        )
                    )
            else:
                # Ordinary line: check if it represents a topic
                # Filter out separators, header metadata, and decorative lines
                is_separator = bool(re.match(r"^[\=\-\_\*\#]{3,}$", line))
                is_header_meta = any(
                    term in line.lower()
                    for term in [
                        "academic year",
                        "total credits",
                        "autonomous",
                        "department of",
                        "course objectives",
                        "course outcomes",
                        "semester",
                        "institute of",
                        "university",
                    ]
                )
                if len(line) < 80 and not line.endswith(".") and not is_separator and not is_header_meta:
                    w_match = weight_pattern.search(line)
                    topic_weight = float(w_match.group(1)) if w_match else None
                    clean_line = weight_pattern.sub("", line).strip(" -:()")
                    if clean_line and clean_line != course_name:
                        current_topics.append(
                            ParsedTopic(
                                name=clean_line,
                                unit=current_unit,
                                subtopics=[],
                                official_weight=topic_weight,
                            )
                        )

        # Fallback if no structured topics detected: split by paragraphs
        if not current_topics:
            warnings.append(
                "Could not find standard unit/bullet markers. Inferred topics from paragraphs."
            )
            for i, line in enumerate(lines[:30]):
                if len(line) > 5 and len(line) < 100:
                    current_topics.append(
                        ParsedTopic(
                            name=line,
                            unit=f"Section {(i // 5) + 1}",
                            subtopics=[],
                            official_weight=None,
                        )
                    )

        # Remove duplicate topics while preserving order
        seen = set()
        deduped_topics = []
        for t in current_topics:
            key = (t.name.lower(), t.unit.lower())
            if key not in seen and len(t.name) > 2:
                seen.add(key)
                deduped_topics.append(t)

        parsed_subject = ParsedSubject(
            name=course_name,
            topics=deduped_topics,
        )

        return SyllabusData(
            source_type=source_type,
            filename=filename,
            course_name=course_name,
            subjects=[parsed_subject],
            warnings=warnings,
        )

    def parse_pdf_file(self, pdf_path: str) -> SyllabusData:
        """Extract text from PDF file and parse structured syllabus."""
        extracted = extract_text_from_pdf(pdf_path)
        return self.parse_text(
            text=extracted["full_text"],
            filename=extracted["filename"],
            source_type="pdf",
        )

    def parse_pdf_bytes(self, pdf_bytes: bytes, filename: str) -> SyllabusData:
        """Extract text from in-memory PDF bytes and parse structured syllabus."""
        extracted = extract_text_from_bytes(pdf_bytes, filename=filename)
        return self.parse_text(
            text=extracted["full_text"],
            filename=filename,
            source_type="pdf",
        )
