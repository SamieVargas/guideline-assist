"""Part 6: post-call QA with labels by construction.

Test set: the 100 untouched conversations of qa_100 (every required step
logged, in guideline order) plus, for each, up to one perturbed copy per
defect kind (core/perturb.py), each keeping its untouched twin. Copies are
made in code from QA_SEED, so the set is identical on every run.

    python evals/run_qa.py --baseline         # no key: the rule QA over the same set
    python evals/run_qa.py --estimate-only
    python evals/run_qa.py                    # keyed: model QA (default sonnet) + the rule row

The untouched false-flag rate is reported first.
"""

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor

from common import add_keyed_args, gate, stamp, today, write
from core import samples
from core.contracts import QA_FLAGS
from core.data import by_id, load_split, render_transcript
from core.estimate import Estimate, call_cost
from core.guidelines import render_section, section_id
from core.metrics import pct, rate
from core.models import DEFAULT_QA, model_id
from core.perturb import EXPECTED, KINDS, perturb
from core.qa import QA_RULES, qa_model, qa_rules

QA_SEED = 20260927


def build_set():
    sample = samples.load("qa_100")
    test = by_id(load_split("test"))
    untouched = [test[i] for i in sample["ids"]]
    perturbed = [x for c in untouched for k in KINDS if (x := perturb(c, k, QA_SEED))]
    return sample, untouched, perturbed


def score(recs) -> dict:
    """recs: {conv, twin, kind (untouched|remove|swap|value), target, statuses: {action: {status, turn}}}"""
    un = [r for r in recs if r["kind"] == "untouched"]
    out = {"n_untouched": len(un), "n_perturbed": len(recs) - len(un)}
    flagged = lambda r: [a for a, s in r["statuses"].items() if s["status"] in QA_FLAGS]  # noqa: E731
    out["false_flag_conversations"] = rate(sum(1 for r in un if flagged(r)), len(un))
    steps_un = [s for r in un for s in r["statuses"].values()]
    out["false_flag_steps"] = rate(sum(1 for s in steps_un if s["status"] in QA_FLAGS), len(steps_un))
    out["recall"], out["detected_any_flag"] = {}, {}
    for k in KINDS:
        rs = [r for r in recs if r["kind"] == k]
        exact = sum(1 for r in rs if any(r["statuses"][a]["status"] == EXPECTED[k] for a in r["target"]))
        loose = sum(1 for r in rs if any(r["statuses"][a]["status"] in QA_FLAGS for a in r["target"]))
        out["recall"][k] = rate(exact, len(rs))
        out["detected_any_flag"][k] = rate(loose, len(rs))
    out["precision"] = {}
    for status in QA_FLAGS:
        tp = fp = 0
        for r in recs:
            for a, s in r["statuses"].items():
                if s["status"] != status:
                    continue
                if r["kind"] != "untouched" and a in r["target"] and EXPECTED[r["kind"]] == status:
                    tp += 1
                else:
                    fp += 1
        out["precision"][status] = rate(tp, tp + fp)
    return out


def render(groups, sample, counts, partial=False) -> str:
    lines = [f"# Post-call QA · {today()} · sample qa_100 (`{sample['sha256'][:12]}`) · perturbation seed {QA_SEED}" + (" · PARTIAL" if partial else ""), "",
             f"Untouched: {counts['untouched']}. Perturbed copies: " + ", ".join(f"{k} {counts[k]}" for k in KINDS)
             + ". A flag is `missed`, `out_of_order` or `wrong_value`.", "",
             "## False flags on untouched conversations (read this first)", "",
             "| QA · model | Conversations with any flag | Steps flagged | Stamp |", "| --- | --- | --- | --- |"]
    for name, s in groups.items():
        lines.append(f"| {name} | {pct(s['false_flag_conversations'])} | {pct(s['false_flag_steps'])} | {stamp(n=s['n_untouched'], model=name, sample=sample)} |")
    lines += ["", "## Recall per defect type (the expected status on the defective step)", "",
              "| QA · model | " + " | ".join(f"{k} → {EXPECTED[k]}" for k in KINDS) + " | " + " | ".join(f"{k}: any flag on the step" for k in KINDS) + " |",
              "| --- " * (1 + 2 * len(KINDS)) + "|"]
    for name, s in groups.items():
        lines.append(f"| {name} | " + " | ".join(pct(s["recall"][k]) for k in KINDS) + " | " + " | ".join(pct(s["detected_any_flag"][k]) for k in KINDS) + " |")
    lines += ["", "## Precision per flag", "", "| QA · model | " + " | ".join(QA_FLAGS) + " |", "| --- " * (1 + len(QA_FLAGS)) + "|"]
    for name, s in groups.items():
        lines.append(f"| {name} | " + " | ".join(pct(s["precision"][f]) for f in QA_FLAGS) + " |")
    lines += ["", "Precision counts every flag of that status across untouched and perturbed conversations; it is a true positive only on the planted step of a copy whose planted defect is that status."]
    return "\n".join(lines)


def rule_records(convs):
    return [_rec(c, qa_rules(c), None) for c in convs]


def _rec(c, statuses, meta):
    pert = c.get("perturbation")
    return {"conv": c["id"], "twin": c.get("twin"), "subflow": c["subflow"], "kind": pert["kind"] if pert else "untouched",
            "target": pert["actions"] if pert else [], "detail": pert["detail"] if pert else "", "statuses": statuses,
            "valid": meta["valid"] if meta else True, "violations": meta["violations"] if meta else [],
            "latency_ms": meta["latency_ms"] if meta else 0, "usage": meta["usage"] if meta else None,
            "cost_usd": meta["cost_usd"] if meta else 0.0}


def main(argv=None, client=None) -> int:
    p = add_keyed_args(argparse.ArgumentParser(description=__doc__.splitlines()[0]))
    p.add_argument("--models", default=DEFAULT_QA)
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--baseline", action="store_true")
    args = p.parse_args(argv)
    sample, untouched, perturbed = build_set()
    convs = untouched + perturbed
    counts = {"untouched": len(untouched), **{k: sum(1 for c in perturbed if c["perturbation"]["kind"] == k) for k in KINDS}}
    rules = rule_records(convs)
    groups = {"rules (no model)": score(rules)}
    if args.baseline:
        md = render(groups, sample, counts)
        print(md)
        write(args.out, f"qa-baseline-{today()}", md, rules)
        return 0
    models = [model_id(m.strip()) for m in args.models.split(",") if m.strip()]
    est = Estimate(f"QA, {len(convs)} conversations x {len(models)} model(s)")
    for mid in models:
        est.add("qa", mid, len(convs), sum(call_cost(mid, uncached_chars=len(QA_RULES) + len(render_section(section_id(c["subflow"])))
                                                   + len(render_transcript(c["turns"])) + 200, out_tokens=350) for c in convs))
    client = gate(est, args, client)
    if client is None:
        return 0 if args.estimate_only else 2
    all_recs, partial = list(rules), False
    try:
        for mid in models:
            def one(c):
                st, meta = qa_model(client, c, model=mid, contract=args.contract, use_cache=not args.no_cache)
                return {**_rec(c, st, meta), "model": mid}
            with ThreadPoolExecutor(max_workers=args.workers) as ex:
                recs = list(ex.map(one, convs))
            all_recs += recs
            groups[f"`{mid}`"] = score(recs)
    except KeyboardInterrupt:
        partial = True
    md = render(groups, sample, counts, partial)
    print(md)
    write(args.out, f"qa-{today()}" + ("-partial" if partial else ""), md, all_recs)
    return 130 if partial else 0


if __name__ == "__main__":
    sys.exit(main())
