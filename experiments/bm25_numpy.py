"""Independent BM25S-inspired experiment; not a homework adapter replacement.

Design reference: https://arxiv.org/abs/2407.03618 (eager sparse scoring).
Original implementation below uses per-term NumPy arrays, candidate-only
accumulation, float64 scores and explicit document-id tie breaking.
"""
from collections import Counter
import math

import numpy as np

from cs329z_hw1.tokenizer import tokenize


def build(docs: list[str]) -> dict:
    postings = {}
    lengths = np.empty(len(docs), dtype=np.float64)
    for doc_id, doc in enumerate(docs):
        tokens = tokenize(doc)
        lengths[doc_id] = len(tokens)
        for term, frequency in Counter(tokens).items():
            ids, counts = postings.setdefault(term, ([], []))
            ids.append(doc_id)
            counts.append(frequency)

    average = float(lengths.mean()) if len(docs) else 0.0
    normalization = 1.5 * (0.25 + 0.75 * lengths / average) if average else lengths
    index = {}
    for term, (ids, counts) in postings.items():
        doc_ids = np.asarray(ids, dtype=np.int64)
        frequencies = np.asarray(counts, dtype=np.float64)
        idf = math.log(1 + (len(docs) - len(ids) + 0.5) / (len(ids) + 0.5))
        contributions = idf * (frequencies * 2.5 / (frequencies + normalization[doc_ids]))
        index[term] = (doc_ids, contributions)
    return index


def search(index: dict, query: str, k: int) -> list[tuple[int, float]]:
    if k <= 0:
        return []
    matches = [index[t] for t in dict.fromkeys(tokenize(query)) if t in index]
    if not matches:
        return []
    if len(matches) == 1:
        candidates, scores = matches[0]
    else:
        ids = np.concatenate([item[0] for item in matches])
        values = np.concatenate([item[1] for item in matches])
        candidates, inverse = np.unique(ids, return_inverse=True)
        scores = np.bincount(inverse, weights=values)

    count = min(k, len(candidates))
    if count < len(candidates):
        cutoff = np.partition(scores, len(scores) - count)[len(scores) - count]
        above = np.flatnonzero(scores > cutoff)
        tied = np.flatnonzero(scores == cutoff)
        # Candidate ids are ascending, including the single-term path.
        chosen = np.concatenate((above, tied[:count - len(above)]))
    else:
        chosen = np.arange(len(candidates))
    order = np.lexsort((candidates[chosen], -scores[chosen]))
    return [(int(candidates[i]), float(scores[i])) for i in chosen[order]]
