"""Call upstream BM25S directly; adapt only the course interface.

Source: https://github.com/xhluca/bm25s (MIT).
Index construction and scoring are performed by the installed library.
Tokenization, query deduplication, no-match filtering and deterministic
top-k ties follow the course contract. This is experimental, not submitted.
"""
import numpy as np

from cs329z_hw1.tokenizer import tokenize


def build(docs: list[str]):
    import bm25s

    tokens = [tokenize(doc) for doc in docs]
    if not any(tokens):
        return None
    # ATIRE TF includes (k1 + 1), with Lucene IDF: exactly the course formula.
    model = bm25s.BM25(
        k1=1.5, b=0.75, method="atire", idf_method="lucene",
        dtype="float64", backend="numpy",
    )
    model.index(tokens, show_progress=False)
    return model


def search(model, query: str, k: int) -> list[tuple[int, float]]:
    if model is None or k <= 0:
        return []
    terms = [t for t in dict.fromkeys(tokenize(query)) if t in model.vocab_dict]
    if not terms:
        return []
    scores = model.get_scores(terms)
    candidates = np.flatnonzero(scores > 0)
    count = min(k, len(candidates))
    if not count:
        return []
    values = scores[candidates]
    if count < len(candidates):
        cutoff = np.partition(values, len(values) - count)[len(values) - count]
        above = candidates[values > cutoff]
        tied = candidates[values == cutoff]
        chosen = np.concatenate((above, tied[:count - len(above)]))
    else:
        chosen = candidates
    order = np.lexsort((chosen, -scores[chosen]))
    return [(int(i), float(scores[i])) for i in chosen[order]]
