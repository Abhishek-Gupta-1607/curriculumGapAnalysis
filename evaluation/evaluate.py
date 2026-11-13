#!/usr/bin/env python3
"""
evaluation/evaluate.py
======================
Stand-alone evaluation runner.

Computes precision, recall, F1, detection rate, and citation coverage
across all 3 demonstration syllabi and prints a structured evaluation report.
"""

import sys
import logging
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tabulate import tabulate
from backend.services.evaluation_service import run_full_evaluation

logging.basicConfig(level=logging.WARNING)


def main():
    print("=" * 80)
    print("CURRICULUM GAP ANALYSIS PIPELINE - BENCHMARK EVALUATION")
    print("=" * 80)
    print("Evaluating against ground truth benchmark (15 known gaps across 3 domains)...\n")

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
    print("\nBenchmark Limitation Statement:")
    print(f"  \"{eval_result.limitation}\"\n")


if __name__ == "__main__":
    main()
