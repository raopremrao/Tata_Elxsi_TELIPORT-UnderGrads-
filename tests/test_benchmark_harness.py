"""Tests for Benchmark Harness and Verdict Generation (Milestone M6)."""

import json
from pathlib import Path
import pandas as pd
from optimize.benchmark import run_benchmark_suite


def test_benchmark_suite_execution():
    test_out = "outputs/benchmark_test"
    summary = run_benchmark_suite(n_seeds=2, output_dir=test_out)

    assert "metadata" in summary
    assert "solvers" in summary
    assert "QUBO_SA" in summary["solvers"]
    assert "Random_Search" in summary["solvers"]

    # Check files created
    assert Path(f"{test_out}/benchmark_summary.json").exists()
    assert Path(f"{test_out}/benchmark_seeds.csv").exists()
    assert Path(f"{test_out}/VERDICT.md").exists()

    df_seeds = pd.read_csv(f"{test_out}/benchmark_seeds.csv")
    assert len(df_seeds) == 8  # 2 seeds * 4 solvers
    assert "optimality_gap_pct" in df_seeds.columns
    assert "runtime_s" in df_seeds.columns

    # Verify verdict text content
    verdict = Path(f"{test_out}/VERDICT.md").read_text(encoding="utf-8")
    assert "Scientific Honesty Statement" in verdict
    assert "QUBO + Vectorized SA" in verdict

