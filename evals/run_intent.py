"""Part 5: conversation-level intent on the frozen intent_300 sample, full
transcript (ACTION lines left out, see core/intent.py), 55 subflows.

    python evals/run_intent.py --baseline        # no key: majority-class baseline, scoring checked
    python evals/run_intent.py --estimate-only
    python evals/run_intent.py                   # keyed, both models
"""

import argparse
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

from common import add_keyed_args, gate, stamp, today, write
from core import samples
from core.data import by_id, load_split, render_transcript
from core.enums import SUBFLOWS
from core.estimate import Estimate, call_cost
from core.guidelines import subflow_menu
from core.intent import CONV_INTENT_RULES, classify
from core.metrics import confused_pairs, macro_f1, mean, pct, rate
from core.models import MODELS, model_id


def score(recs) -> dict:
    gold = [r["gold"] for r in recs]
    pred = [r["pred"] or "(none)" for r in recs]
    return {"n": len(recs), "accuracy": rate(sum(g == p for g, p in zip(gold, pred)), len(recs)),
            "macro_f1": macro_f1(gold, pred, labels=SUBFLOWS), "confused": confused_pairs(gold, pred, 5),
            "validator_pass": rate(sum(bool(r["valid"]) for r in recs), len(recs)),
            "latency_mean": mean([r["latency_ms"] for r in recs]), "cost": round(sum(r["cost_usd"] for r in recs), 4)}


def render(groups, sample, partial=False) -> str:
    lines = [f"# Conversation-level intent · {today()} · sample intent_300 (`{sample['sha256'][:12]}`)" + (" · PARTIAL" if partial else ""), "",
             "Full transcript without ACTION lines, one of 55 subflows. Macro-F1 averages over the subflows present in the sample.", "",
             "| Model | Accuracy | Macro-F1 | Top confused pairs (count) | Validator pass | Mean latency | Cost (run) | Stamp |",
             "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for model, s in groups.items():
        conf = "; ".join(f"{a} ↔ {b} ({n})" for (a, b), n in s["confused"]) or "none"
        lines.append(f"| `{model}` | {pct(s['accuracy'])} | {s['macro_f1']} | {conf} | {pct(s['validator_pass'])} | "
                     f"{s['latency_mean']} ms | ${s['cost']:.2f} | {stamp(n=s['n'], model=model, sample=sample)} |")
    return "\n".join(lines)


def main(argv=None, client=None) -> int:
    p = add_keyed_args(argparse.ArgumentParser(description=__doc__.splitlines()[0]))
    p.add_argument("--models", default=",".join(MODELS))
    p.add_argument("--workers", type=int, default=4, help="parallel calls; latency here is not a headline number")
    p.add_argument("--baseline", action="store_true")
    args = p.parse_args(argv)
    sample = samples.load("intent_300")
    test = by_id(load_split("test"))
    convs = [test[i] for i in sample["ids"]]
    if args.baseline:
        train_major = Counter(c["subflow"] for c in load_split("train")).most_common(1)[0][0]
        recs = [{"conv": c["id"], "gold": c["subflow"], "pred": train_major, "valid": True, "latency_ms": 0, "cost_usd": 0.0} for c in convs]
        md = render({f"majority class from train ({train_major})": score(recs)}, sample).replace("# Conversation", "# Baseline · conversation", 1)
        print(md)
        write(args.out, f"intent-baseline-{today()}", md, recs)
        return 0
    models = [model_id(m.strip()) for m in args.models.split(",") if m.strip()]
    est = Estimate(f"conversation intent, {len(convs)} conversations x {len(models)} model(s)")
    for mid in models:
        est.add("intent", mid, len(convs), sum(call_cost(mid, uncached_chars=len(CONV_INTENT_RULES) + len(subflow_menu())
                                                         + len(render_transcript(c["turns"], include_actions=False)) + 60, out_tokens=15) for c in convs))
    client = gate(est, args, client)
    if client is None:
        return 0 if args.estimate_only else 2
    groups, all_recs, partial = {}, [], False
    try:
        for mid in models:
            def one(c):
                pred, meta = classify(client, c, model=mid, contract=args.contract, use_cache=not args.no_cache)
                return {"conv": c["id"], "gold": c["subflow"], "pred": pred, "model": mid, "valid": meta["valid"],
                        "latency_ms": meta["latency_ms"], "usage": meta["usage"], "cost_usd": meta["cost_usd"]}
            with ThreadPoolExecutor(max_workers=args.workers) as ex:
                recs = list(ex.map(one, convs))
            all_recs += recs
            groups[mid] = score(recs)
            print(f"  {mid}: accuracy {pct(groups[mid]['accuracy'])}", flush=True)
    except KeyboardInterrupt:
        partial = True
    md = render(groups, sample, partial)
    print(md)
    write(args.out, f"intent-{today()}" + ("-partial" if partial else ""), md, all_recs)
    return 130 if partial else 0


if __name__ == "__main__":
    sys.exit(main())
