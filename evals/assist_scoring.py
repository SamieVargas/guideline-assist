"""Scoring for turn-level assist records, shared by the Part 3/4 runner, the
shadow table and the readout. A record is one call point:

  {conv, subflow, i, kind: action|no_action, gold_action, gold_values,
   pred: {intent, section_id, next_action, slot_values, suggestion},
   valid, citation_valid, retries, latency_ms, usage, cost_usd, calls}
"""

from collections import defaultdict

from core.metrics import mean, percentile, rate
from core.points import value_recall, values_match

POSITION_BUCKETS = ((0, 4, "turns 0–4"), (5, 9, "5–9"), (10, 14, "10–14"), (15, 10**6, "15+"))

# Assist triggers per conversation in a deployment: once per agent-side
# turn (an agent utterance or an agent action). Measured on the test split
# by evals/ingest.py: 9.51 agent utterances + 3.59 actions.
TRIGGERS_PER_CONVERSATION = 9.51 + 3.59


def bucket(i):
    return next(label for lo, hi, label in POSITION_BUCKETS if lo <= i <= hi)


def turns_to_stable(recs):
    """The turn index from which the intent is right at every later call
    point in the conversation; None if the last call point is wrong."""
    recs = sorted(recs, key=lambda r: r["i"])
    stable = None
    for r in reversed(recs):
        if r["pred"]["intent"] == r["subflow"]:
            stable = r["i"]
        else:
            break
    return stable


def score(records) -> dict:
    act = [r for r in records if r["kind"] == "action"]
    noact = [r for r in records if r["kind"] == "no_action"]
    by_conv = defaultdict(list)
    for r in records:
        by_conv[r["conv"]].append(r)
    stable = [turns_to_stable(v) for v in by_conv.values()]
    named = [r for r in act if r["pred"]["next_action"] == r["gold_action"] and r["gold_values"]]
    lat = [r["latency_ms"] for r in records]
    usage = [r["usage"] for r in records]
    per_call_cost = mean([r["cost_usd"] for r in records])
    out = {
        "n_points": len(records), "n_action": len(act), "n_no_action": len(noact), "n_conversations": len(by_conv),
        "intent": rate(sum(r["pred"]["intent"] == r["subflow"] for r in records), len(records)),
        "intent_by_position": {label: rate(sum(r["pred"]["intent"] == r["subflow"] for r in records if bucket(r["i"]) == label),
                                           sum(1 for r in records if bucket(r["i"]) == label)) for *_, label in POSITION_BUCKETS},
        "turns_to_stable": {"median": percentile([s for s in stable if s is not None], 50),
                            "mean": mean([s for s in stable if s is not None]),
                            "never": sum(1 for s in stable if s is None), "n": len(stable)},
        "next_action": rate(sum(r["pred"]["next_action"] == r["gold_action"] for r in act), len(act)),
        "none_yet_on_action_points": rate(sum(r["pred"]["next_action"] == "none_yet" for r in act), len(act)),
        "slot_exact": rate(sum(values_match(r["pred"]["slot_values"], r["gold_values"]) for r in named), len(named)),
        "slot_value_recall": mean([value_recall(r["pred"]["slot_values"], r["gold_values"]) for r in named]),
        "false_alarm": rate(sum(r["pred"]["next_action"] != "none_yet" for r in noact), len(noact)),
        "citation_valid": rate(sum(bool(r["citation_valid"]) for r in records), len(records)),
        "validator_pass": rate(sum(bool(r["valid"]) for r in records), len(records)),
        "retries": sum(r.get("retries", 0) for r in records),
        "latency_p50": percentile(lat, 50), "latency_p95": percentile(lat, 95),
        "input_tokens_mean": mean([u["input_tokens"] + u["cache_creation_input_tokens"] + u["cache_read_input_tokens"] for u in usage]),
        "uncached_input_mean": mean([u["input_tokens"] for u in usage]),
        "cache_read_total": sum(u["cache_read_input_tokens"] for u in usage),
        "cache_write_total": sum(u["cache_creation_input_tokens"] for u in usage),
        "cache_read_share": None,
        "cost_per_turn": per_call_cost,
        "cost_per_1000_conversations": round(per_call_cost * TRIGGERS_PER_CONVERSATION * 1000, 2) if per_call_cost is not None else None,
        "calls": sum(r.get("calls", 1) for r in records),
        "from_cache": sum(1 for r in records if r.get("from_cache")),
    }
    total_in = sum(u["input_tokens"] + u["cache_creation_input_tokens"] + u["cache_read_input_tokens"] for u in usage)
    out["cache_read_share"] = round(out["cache_read_total"] / total_in, 4) if total_in else None
    return out
