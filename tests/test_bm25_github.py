"""Reuse course tests against the actual upstream BM25S library.

Run separately: uv run --with bm25s==0.3.2 pytest tests/test_bm25_github.py -v -s
The dependency is temporary; pyproject.toml and uv.lock are not changed.
"""
import pytest

pytest.importorskip("bm25s", reason="Use uv run --with bm25s==0.3.2 pytest ...")

from cs329z_hw1 import adapters
from experiments import bm25_upstream
from tests import test_bm25 as course


@pytest.fixture(autouse=True)
def experimental_implementation(monkeypatch):
    monkeypatch.setattr(adapters, "run_bm25_build", bm25_upstream.build)
    monkeypatch.setattr(adapters, "run_bm25_search", bm25_upstream.search)
    # The course caches its archive index. Isolate that cache for this file
    # so running both files together cannot mix baseline/experimental data.
    monkeypatch.setattr(course, "_archive_index", _experimental_archive_index)


_experimental_archive_index = {}

# Reuse the original test functions, including their archive fixture and
# exact score, ranking, recall and performance assertions.
for _name, _test in vars(course).items():
    if _name.startswith("test_") and callable(_test):
        globals()[_name] = _test
