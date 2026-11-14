"""Tests for Q-0148 encyclopedia search latency benchmark."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from knowledge.medical.search_benchmark import run_search_latency_benchmark


def test_search_latency_at_119_catalog_size_is_under_budget() -> None:
    report = run_search_latency_benchmark(catalog_size=119, iterations=100, query="SYN-42")
    assert report["catalog_size"] == 119
    assert report["iterations"] == 100
    assert report["is_synthetic_benchmark_fixture"] is True
    assert report["is_real_medical_data"] is False
    assert report["last_matches"] == 1
    assert report["p95_ms"] < 50.0
    assert report["min_ms"] <= report["p50_ms"] <= report["p95_ms"] <= report["max_ms"]
