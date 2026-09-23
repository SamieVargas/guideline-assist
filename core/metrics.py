"""Small, dependency-free metrics: rates with their n, percentiles, macro-F1,
the most-confused pairs, Cohen's kappa."""

import math
from collections import Counter


def rate(hits, n):
    return {"k": hits, "n": n, "rate": round(hits / n, 4) if n else None}


def mean(vals):
    vals = [v for v in vals if v is not None]
    return round(sum(vals) / len(vals), 4) if vals else None


def percentile(vals, p):
    """Nearest-rank percentile, the conservative choice for p95 latency."""
    vals = sorted(v for v in vals if v is not None)
    if not vals:
        return None
    k = max(1, math.ceil(p / 100 * len(vals)))
    return vals[k - 1]


def macro_f1(gold, pred, labels=None):
    labels = sorted(set(gold) | set(pred)) if labels is None else list(labels)
    labels = [l for l in labels if l in set(gold)]  # classes present in the gold set
    f1s = []
    for l in labels:
        tp = sum(1 for g, p in zip(gold, pred) if g == l and p == l)
        fp = sum(1 for g, p in zip(gold, pred) if g != l and p == l)
        fn = sum(1 for g, p in zip(gold, pred) if g == l and p != l)
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        f1s.append(2 * prec * rec / (prec + rec) if prec + rec else 0.0)
    return round(sum(f1s) / len(f1s), 4) if f1s else None


def confused_pairs(gold, pred, top=5):
    """Unordered pairs {a, b} ranked by how often one was predicted for the other."""
    c = Counter(tuple(sorted((g, p))) for g, p in zip(gold, pred) if g != p)
    return c.most_common(top)


def cohen_kappa(a, b):
    n = len(a)
    if not n:
        return None
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return round((po - pe) / (1 - pe), 4) if pe < 1 else None


def pct(x):
    if isinstance(x, dict):
        return "n/a" if x.get("rate") is None else f"{x['rate'] * 100:.1f}% ({x['k']}/{x['n']})"
    return "n/a" if x is None else f"{x * 100:.1f}%"
