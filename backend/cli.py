"""
backend/cli.py
==============
Command-Line Interface (CLI) for Curriculum Gap Analysis Pipeline.

WHAT THIS FILE DOES:
  Enables running the complete 6-agent pipeline, framework ingestion,
  and benchmark evaluations directly from the command line without
  launching the web frontend.

USAGE EXAMPLES:
  # 1. Run sample analysis on built-in data science syllabus:
  python -m backend.cli --domain "Data Science" --sample

  # 2. Run analysis on a user-provided PDF syllabus:
  python -m backend.cli --file path/to/syllabus.pdf --domain "Web Development"

  # 3. Ingest all framework PDFs into ChromaDB & SQLite:
  python -m backend.cli --ingest

  # 4. Run automated benchmark evaluation against ground truth:
  python -m backend.cli --evaluate
"""

import sys
import os
import argparse
import logging
from pathlib import Path
from tabulate import tabulate

from backend.config import settings, PROJECT_ROOT
from backend.core.tracing import get_run_events
from backend.database.db import SessionLocal
from backend.agents.curriculum_coordinator import CurriculumCoordinator
from backend.rag.ingestion import ingest_all_frameworks
from backend.services.evaluation_service import run_full_evaluation

# Suppress verbose dependency info logs in CLI output
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Curriculum Gap Analysis Pipeline - Evidence-Based Multi-Agent AI System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--domain",
        type=str,
        default="Data Science",
        help="Target domain: 'Data Science', 'Web Development', or 'Cloud and DevOps'",
    )
    parser.add_argument(
        "--file",
        type=str,
        help="Path to syllabus PDF document to analyze",
    )
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Run analysis using the built-in sample syllabus for the specified domain",
    )
    parser.add_argument(
        "--ingest",
        action="store_true",
        help="Ingest all framework documents into ChromaDB vector database and SQLite",
    )
    parser.add_argument(
        "--evaluate",
        action="store_true",
        help="Run full benchmark evaluation against ground truth across all 3 domains",
    )
    parser.add_argument(
        "--covered-threshold",
        type=float,
        default=settings.COVERED_THRESHOLD,
        help=f"Similarity threshold for COVERED status (default: {settings.COVERED_THRESHOLD})",
    )
    parser.add_argument(
        "--partial-threshold",
        type=float,
        default=settings.PARTIAL_THRESHOLD,
        help=f"Similarity threshold for PARTIAL status (default: {settings.PARTIAL_THRESHOLD})",
    )

    args = parser.parse_args()

    # -------------------------------------------------------------
    # COMMAND: --ingest
    # -------------------------------------------------------------
    if args.ingest:
        print("\n=======================================================")
        print("INGESTING FRAMEWORK DOCUMENTS INTO CHROMADB & SQLITE")
        print("=======================================================\n")
        results = ingest_all_frameworks()
        table = [
            [r["domain"], r["name"], f"{r['chunks']} chunks", r["status"]]
            for r in results
        ]
        print(tabulate(table, headers=["Domain", "Document", "Chunks", "Status"], tablefmt="fancy_grid"))
        print("\nFramework ingestion complete.\n")
        return

    # -------------------------------------------------------------
    # COMMAND: --evaluate
    # -------------------------------------------------------------
    if args.evaluate:
        print("\n=======================================================")
        print("RUNNING BENCHMARK EVALUATION ACROSS ALL DOMAINS")
        print("=======================================================\n")
        eval_result = run_full_evaluation()
        table_data = []
        for d in eval_result.per_domain:
            table_data.append([
                d.domain,
                f"{d.correctly_detected}/{d.total_known_gaps}",
                d.false_positives,
                d.false_negatives,
                f"{d.precision * 100:.1f}%",
                f"{d.recall * 100:.1f}%",
                f"{d.f1_score * 100:.1f}%",
                f"{d.detection_rate:.1f}%",
                f"{d.citation_coverage_after:.1f}%",
            ])
        ov = eval_result.overall
        table_data.append([
            "OVERALL",
            f"{ov.correctly_detected}/{ov.total_known_gaps}",
            ov.false_positives,
            ov.false_negatives,
            f"{ov.precision * 100:.1f}%",
            f"{ov.recall * 100:.1f}%",
            f"{ov.f1_score * 100:.1f}%",
            f"{ov.detection_rate:.1f}%",
            f"{ov.citation_coverage_after:.1f}%",
        ])
        headers = [
            "Domain", "Detected / Known", "FP", "FN",
            "Precision", "Recall", "F1-Score", "Detection Rate", "Citation Cov."
        ]
        print(tabulate(table_data, headers=headers, tablefmt="fancy_grid"))
        print(f"\nLimitation: \"{eval_result.limitation}\"\n")
        return

    # -------------------------------------------------------------
    # COMMAND: Analyze Syllabus (--sample or --file)
    # -------------------------------------------------------------
    target_file = None
    domain = args.domain

    if args.sample:
        # Match domain to sample syllabus
        d_lower = domain.lower()
        if "data" in d_lower:
            domain = "Data Science"
            target_file = PROJECT_ROOT / "data" / "syllabi" / "data_science.pdf"
        elif "web" in d_lower:
            domain = "Web Development"
            target_file = PROJECT_ROOT / "data" / "syllabi" / "web_development.pdf"
        elif "cloud" in d_lower or "devops" in d_lower:
            domain = "Cloud and DevOps"
            target_file = PROJECT_ROOT / "data" / "syllabi" / "cloud_devops.pdf"
        else:
            print(f"Error: Unknown domain '{domain}'. Choose 'Data Science', 'Web Development', or 'Cloud and DevOps'.")
            sys.exit(1)
    elif args.file:
        target_file = Path(args.file)
        if not target_file.exists():
            print(f"Error: File not found: {args.file}")
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(0)

    print("\n=======================================================")
    print("CURRICULUM GAP ANALYSIS PIPELINE")
    print("=======================================================")
    print(f"Domain:    {domain}")
    print(f"Syllabus:  {target_file.name}")
    print(f"Mode:      {settings.mode_label}")
    print("=======================================================\n")

    coordinator = CurriculumCoordinator()
    print("Executing sequential 6-agent pipeline...")

    state = coordinator.run_pipeline(
        domain=domain,
        syllabus_input=str(target_file),
        is_pdf=True,
        filename=target_file.name,
        covered_threshold=args.covered_threshold,
        partial_threshold=args.partial_threshold,
    )

    # -------------------------------------------------------------
    # Display Real Agent Execution Sequence
    # -------------------------------------------------------------
    print("\n--- AGENT EXECUTION SEQUENCE ---")
    db = SessionLocal()
    try:
        events = get_run_events(db, state.run_id)
        trace_table = [
            [ev["step_number"], ev["agent_name"], ev["status"], f"{ev['duration_ms'] or 0} ms", ev["output_summary"][:55] + "..."]
            for ev in events
        ]
        print(tabulate(trace_table, headers=["Step", "Agent", "Status", "Duration", "Output Summary"], tablefmt="simple"))
    finally:
        db.close()

    # -------------------------------------------------------------
    # Display Summary Results
    # -------------------------------------------------------------
    stats = state.statistics
    print("\n--- CURRICULUM COVERAGE SUMMARY ---")
    print(f"  Run ID:                    {state.run_id}")
    print(f"  Status:                    {state.status}")
    print(f"  Total Framework Skills:    {stats['total_framework_skills']}")
    print(f"  Covered Skills:            {stats['covered']}")
    print(f"  Partially Covered Skills:  {stats['partial']}")
    print(f"  Missing Skills:            {stats['missing']}")
    print(f"  Total Recommendations:     {stats['total_recommendations']}")
    print(f"  Approved by Reviewer:      {stats['approved_recommendations']}")
    print(f"  Rejected by Reviewer:      {stats['rejected_recommendations']}")

    # -------------------------------------------------------------
    # Display Approved Recommendations
    # -------------------------------------------------------------
    if state.approved_recommendations:
        print("\n--- APPROVED CURRICULUM RECOMMENDATIONS ---")
        rec_table = []
        for r in state.approved_recommendations:
            rec_table.append([
                r.framework_id,
                r.topic,
                f"{r.recommended_weight} ({r.weight_type})",
                r.level,
                r.resource[:30],
                r.evidence_id,
            ])
        print(tabulate(rec_table, headers=["ID", "Topic", "Weight", "Level", "Learning Resource", "Evidence ID"], tablefmt="fancy_grid"))

    if state.rejected_recommendations:
        print("\n--- REJECTED RECOMMENDATIONS ---")
        rej_table = [
            [r.framework_id, r.topic, r.evidence_id]
            for r in state.rejected_recommendations
        ]
        print(tabulate(rej_table, headers=["ID", "Topic", "Evidence ID"], tablefmt="fancy_grid"))

    print("\nAnalysis run complete.")
    print(f"Results stored in SQLite: {settings.DATABASE_URL}\n")


if __name__ == "__main__":
    main()
