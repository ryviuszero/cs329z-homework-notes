"""Run: uv run python -m experiments.compare_bm25

Runs the unchanged official BM25 tests against the experimental functions
in this process only, then compares both implementations on identical data.
No network, model calls, dependencies or homework files are changed.
"""
import gc
import statistics
import time
from unittest.mock import patch

import numpy as np
import pytest

from cs329z_hw1 import adapters, data
from experiments import bm25_numpy
from tests.helpers import load_fixture


def benchmark(build, search, docs, queries):
    build_times = []
    for _ in range(3):
        gc.collect()
        start = time.perf_counter()
        index = build(docs)
        build_times.append(time.perf_counter() - start)
        del index
    index = build(docs)
    for query in queries:
        search(index, query, 10)
    query_times = []
    for _ in range(7):
        start = time.perf_counter()
        for query in queries:
            search(index, query, 10)
        query_times.append((time.perf_counter() - start) / len(queries))
    return index, statistics.median(build_times), statistics.median(query_times)


def main():
    print("Experimental implementation: unchanged official tests", flush=True)
    with patch.object(adapters, "run_bm25_build", bm25_numpy.build), patch.object(
        adapters, "run_bm25_search", bm25_numpy.search
    ):
        status = pytest.main(["tests/test_bm25.py", "-s", "--tb=short"])
    if status:
        raise SystemExit(status)

    # Boundary cases supplement the course tests, especially cutoff ties.
    for docs in ([], ["", ""], ["apple"] * 20, ["apple banana", "apple", "banana", ""]):
        old = adapters.run_bm25_build(docs)
        new = bm25_numpy.build(docs)
        for query in ("", "missing", "apple", "apple banana", "APPLE apple"):
            for k in (-1, 0, 1, 3, 50):
                expected = adapters.run_bm25_search(old, query, k)
                actual = bm25_numpy.search(new, query, k)
                assert [d for d, _ in actual] == [d for d, _ in expected]
                np.testing.assert_allclose([s for _, s in actual], [s for _, s in expected], atol=1e-12)

    docs = [data.email_text(email) for email in data.load_emails()]
    queries = [item["query"] for item in load_fixture("bm25_queries.json")]
    print(f"Same-machine comparison: {len(docs)} documents, {len(queries)} queries", flush=True)
    baseline, old_build, old_query = benchmark(adapters.run_bm25_build, adapters.run_bm25_search, docs, queries)
    optimized, new_build, new_query = benchmark(bm25_numpy.build, bm25_numpy.search, docs, queries)
    for query in queries:
        expected = adapters.run_bm25_search(baseline, query, 50)
        actual = bm25_numpy.search(optimized, query, 50)
        assert [d for d, _ in actual] == [d for d, _ in expected], query
        np.testing.assert_allclose([s for _, s in actual], [s for _, s in expected], rtol=1e-12, atol=1e-12)
    print("Top-50 document order and scores match for all archive queries.")
    print("Build: median of 3 runs; query: median of 7 warmed batches; excludes file loading.")
    print(f"Baseline: build {old_build:.3f} s; query {old_query * 1000:.3f} ms")
    print(f"NumPy:    build {new_build:.3f} s; query {new_query * 1000:.3f} ms")
    print(f"Speed ratio baseline/NumPy: build {old_build / new_build:.2f}x; query {old_query / new_query:.2f}x")


if __name__ == "__main__":
    main()
