"""Encyclopedia keyword search latency benchmark at intended catalog size (Q-0148)."""

from __future__ import annotations

import math
import time
from typing import Any

from knowledge.medical.encyclopedia_search import search_encyclopedia


def build_synthetic_benchmark_catalog(size: int = 119) -> list[dict[str, Any]]:
    """Build a clearly labeled synthetic benchmark catalog (not medical content)."""
    systems = ["neuro-ocular", "cardiovascular", "musculoskeletal", "vestibular", "immune_hematopoietic"]
    entries: list[dict[str, Any]] = []
    for idx in range(size):
        sys_name = systems[idx % len(systems)]
        entries.append(
            {
                "condition_id": f"BENCH-{idx:012d}",
                "canonical_title": f"Benchmark Condition {idx} ({sys_name})",
                "synonyms": [f"SYN-{idx}", f"ALT-{idx % 17}"],
                "body_systems": [sys_name],
                "symptoms": [f"symptom_{idx % 23}", "visual acuity shift" if idx % 7 == 0 else "fatigue"],
                "overview": f"Synthetic benchmark fixture entry {idx} for latency measurement only.",
                "verification_state": "READY",
                "review_state": "APPROVED",
                "is_synthetic_benchmark_fixture": True,
            }
        )
    return entries


def run_search_latency_benchmark(
    *,
    catalog_size: int = 119,
    iterations: int = 100,
    query: str = "SYN-42",
    body_system: str | None = None,
) -> dict[str, Any]:
    """Measure search_encyclopedia query latency across repeated runs."""
    catalog = build_synthetic_benchmark_catalog(catalog_size)
    latencies_ms: list[float] = []
    last_matches = 0

    for _ in range(iterations):
        t0 = time.perf_counter()
        res = search_encyclopedia(catalog, query=query, body_system=body_system)
        t1 = time.perf_counter()
        latencies_ms.append((t1 - t0) * 1000.0)
        last_matches = res["total_matches"]

    latencies_ms.sort()
    p50_idx = min(len(latencies_ms) - 1, math.floor(0.50 * len(latencies_ms)))
    p95_idx = min(len(latencies_ms) - 1, math.floor(0.95 * len(latencies_ms)))

    return {
        "catalog_size": catalog_size,
        "iterations": iterations,
        "is_synthetic_benchmark_fixture": True,
        "is_real_medical_data": False,
        "last_matches": last_matches,
        "min_ms": round(latencies_ms[0], 4),
        "p50_ms": round(latencies_ms[p50_idx], 4),
        "p95_ms": round(latencies_ms[p95_idx], 4),
        "max_ms": round(latencies_ms[-1], 4),
    }
