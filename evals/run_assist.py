"""Parts 3 and 4: the turn-level assist on the frozen assist_100 sample,
both context arms, both pinned models.

    python evals/run_assist.py --baseline              # no key: the guideline-order baseline, scoring checked end to end
    python evals/run_assist.py --estimate-only         # print what a keyed run would cost
    python evals/run_assist.py                         # keyed: arms A,B x models haiku,sonnet
    python evals/run_assist.py --arms A --models haiku --limit 5   # a small keyed smoke run

Call points (core/points.py): every gold ACTION turn, plus a matched,
seeded set of agent turns where nothing is due before the customer speaks
again. Calls run one at a time so latency is not measured under
self-inflicted contention, and so arm A's cached prefix stays warm.

Ctrl+C writes what finished to a -partial file.
"""

import argparse
import json
import re
import sys
from pathlib import Path

from common import add_keyed_args, gate, stamp, today, write
from assist_scoring import TRIGGERS_PER_CONVERSATION, POSITION_BUCKETS, score
from core import samples
from core.assist import ASSIST_RULES, INTENT_RULES, assist
from core.data import by_id, load_split, render_transcript
from core.estimate import Estimate, call_cost
from core.guidelines import render_library, render_section, section_id, subflow_menu
from core.metrics import pct
from core.models import MODELS, model_id, provider
from core.points import guideline_next, points_for
from core.validate import citation_valid, validate_assist

POINT_SEED = 20260923


def load_points(sample_name, limit=None):
    rec = samples.load(sample_name)
    test = by_id(load_split("test"))
    convs = [test[i] for i in rec["ids"]][: limit or None]
    return rec, convs, [(c, p) for c in convs for p in points_for(c, POINT_SEED)]


def estimate(points, arms, models) -> Estimate:
    est = Estimate(f"assist, {len(points)} call points x {len(arms)} arm(s) x {len(models)} model(s)")
    lib = len(ASSIST_RULES) + len(render_library()) + 20
    for m in models:
        mid = model_id(m)
        for arm in arms:
            usd = 0.0
            for n, (c, p) in enumerate(points):
                ctx = len(render_transcript(c["turns"][: p["i"]])) + 80
                if arm == "A":
                    usd += call_cost(mid, uncached_chars=ctx, cached_chars=lib, out_tokens=90, cache_hit=n > 0)
                else:
                    usd += call_cost(mid, uncached_chars=len(INTENT_RULES) + len(subflow_menu()) + ctx, out_tokens=15)
                    usd += call_cost(mid, uncached_chars=len(ASSIST_RULES) + len(render_section(section_id(c["subflow"]))) + ctx, out_tokens=90)
            est.add(f"arm {arm}", mid, len(points) * (1 if arm == "A" else 2), usd)
            if arm == "A" and provider(mid) == "google":
                miss = sum(call_cost(mid, uncached_chars=lib + len(render_transcript(c["turns"][: p["i"]])) + 80, out_tokens=90)
                           for c, p in points)
                est.worst_extra += miss - usd
                est.notes.append(f"{mid} caches implicitly and without a guarantee; arm A at ~${miss:,.2f} if the cache never hits. "
                                 "Its id and prices in core/models.py are unconfirmed; check them on ai.google.dev first.")
    return est


def baseline_records(points):
    """The guideline-order baseline: told the gold intent, it suggests the
    first required step not yet done. No model, no latency."""
    recs = []
    for c, p in points:
        nxt = guideline_next(c, p["i"])
        pred = {"intent": c["subflow"], "section_id": section_id(c["subflow"]), "next_action": nxt or "none_yet",
                "slot_values": [], "suggestion": "baseline"}
        v = validate_assist(pred)
        recs.append(_record(c, p, pred, {"valid": not v, "violations": v, "retries": 0, "latency_ms": 0.0, "calls": 0,
                                         "usage": {k: 0 for k in ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")},
                                         "cost_usd": 0.0, "from_cache": False}, arm="baseline", model="none"))
    return recs


def _record(c, p, pred, meta, *, arm, model):
    return {"conv": c["id"], "subflow": c["subflow"], "i": p["i"], "kind": p["kind"], "gold_action": p["gold_action"],
            "gold_values": p["gold_values"], "arm": arm, "model": model, "pred": pred, "valid": meta["valid"],
            "violations": meta["violations"], "first_violations": meta.get("first_violations", []),
            "citation_valid": citation_valid(pred, validate_assist(pred)), "retries": meta["retries"],
            "latency_ms": meta["latency_ms"], "calls": meta["calls"], "usage": meta["usage"], "cost_usd": meta["cost_usd"],
            "from_cache": meta["from_cache"]}


def run_keyed(client, points, arms, models, args):
    recs, done = [], 0
    try:
        for m in models:
            mid = model_id(m)
            for arm in arms:
                for c, p in points:
                    pred, meta = assist(client, c["turns"][: p["i"]], arm=arm, model=mid, contract=args.contract,
                                        use_cache=not args.no_cache)
                    recs.append(_record(c, p, pred, meta, arm=arm, model=mid))
                    done += 1
                    print(f"  {mid} arm {arm} {c['id']}@{p['i']:<3} gold={p['gold_action']:<18} pred={pred['next_action']:<18} "
                          f"{meta['latency_ms']:>7.0f} ms{' (cached)' if meta['from_cache'] else ''}", flush=True)
    except KeyboardInterrupt:
        print(f"\ninterrupted after {done} calls; writing the partial table", file=sys.stderr)
        return recs, True
    return recs, False


def render(groups, sample, n_convs, partial=False, run_date=None):
    head = f"# Assist · {run_date or today()} · sample assist_100 (`{sample['sha256'][:12]}`, {n_convs} conversations)" + (" · PARTIAL" if partial else "")
    lines = [head, "",
             "## Part 3 · context ablation", "",
             "Arm A: the full guideline library in a cached system prefix, one call a turn. Arm B: an intent call, then only that subflow's section in context. "
             f"Latency is per turn (all calls that turn, retries included). Cost per 1,000 conversations = mean cost per turn x {TRIGGERS_PER_CONVERSATION:.2f} "
             "assist triggers per conversation (agent utterances + agent actions per test conversation) x 1,000.", "",
             "| Arm · model | Next action | Intent | Cache reads (tokens, share of input) | Mean input tokens / turn (uncached part) | p50 / p95 latency | Cost / 1,000 conversations | Stamp |",
             "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for (arm, model), s in groups.items():
        lat = "n/a (no model)" if arm == "baseline" else f"{s['latency_p50']:.0f} / {s['latency_p95']:.0f} ms"
        lines.append(f"| {arm} · `{model}` | {pct(s['next_action'])} | {pct(s['intent'])} | {s['cache_read_total']:,} ({pct(s['cache_read_share'])}) | "
                     f"{s['input_tokens_mean']} ({s['uncached_input_mean']}) | {lat} | ${s['cost_per_1000_conversations']:,.2f} | "
                     f"{stamp(n=s['n_points'], model=model, sample=sample)} |")
    lines += ["", "## Part 4 · assist evals (turn level)", "",
              "| Arm · model | Intent (all points) | " + " | ".join(f"Intent {lbl}" for *_, lbl in POSITION_BUCKETS)
              + " | Turns to stable intent (median / mean, never) | Next action (action points) | Slots exact (name right) | Slot value recall | `none_yet` false alarms (no-action points) | of which early (the agent's next action) | `none_yet` on action points | Citation valid | Validator pass · retries |",
              "| --- " * (12 + len(POSITION_BUCKETS)) + "|"]
    for (arm, model), s in groups.items():
        t = s["turns_to_stable"]
        lines.append(f"| {arm} · `{model}` | {pct(s['intent'])} | " + " | ".join(pct(s['intent_by_position'][lbl]) for *_, lbl in POSITION_BUCKETS)
                     + f" | {t['median']} / {t['mean']}, never {t['never']}/{t['n']} | {pct(s['next_action'])} | {pct(s['slot_exact'])} | "
                     f"{pct(s['slot_value_recall'])} | {pct(s['false_alarm'])} | {pct(s['false_alarm_early'])} | {pct(s['none_yet_on_action_points'])} | {pct(s['citation_valid'])} | "
                     f"{pct(s['validator_pass'])} · {s['retries']} |")
    lines += ["", "A no-action point is an agent turn after which nothing is due before the customer speaks again. A false alarm there is \"early\" when the "
              "suggested action is the one the agent took next, after the customer replied: premature rather than wrong.",
              "", "Stamp per row: " + "; ".join(f"{a}·{m}: {stamp(n=s['n_points'], model=m, sample=sample)} "
                                              f"({s['n_action']} action points, {s['n_no_action']} no-action points)" for (a, m), s in groups.items())]
    return "\n".join(lines)


def rescore(path) -> int:
    """Rebuild an earlier run's markdown from its JSON records with the
    current scoring code, keeping the run's date. No model call."""
    path = Path(path)
    recs = json.loads(path.read_text(encoding="utf-8"))["records"]
    sample = samples.load("assist_100")
    lookup = by_id(load_split("test"))
    groups = {}
    for r in recs:
        groups.setdefault((r["arm"], r["model"]), []).append(r)
    groups = {k: score(v, lookup) for k, v in groups.items()}
    run_date = re.search(r"\d{4}-\d{2}-\d{2}", path.name).group(0)
    md = render(groups, sample, len({r["conv"] for r in recs}), "partial" in path.name, run_date=run_date)
    if path.name.startswith("assist-baseline"):
        md = md.replace("# Assist", "# Assist baseline (guideline order, gold intent given)", 1)
    path.with_suffix(".md").write_text(md.rstrip() + "\n", encoding="utf-8")
    print(md)
    print(f"rewrote {path.with_suffix('.md').name} from {path.name}")
    return 0


def main(argv=None, client=None) -> int:
    p = add_keyed_args(argparse.ArgumentParser(description=__doc__.splitlines()[0]))
    p.add_argument("--sample", default="assist_100")
    p.add_argument("--arms", default="A,B")
    p.add_argument("--models", default=",".join(MODELS))
    p.add_argument("--limit", type=int, default=None, help="first N conversations of the sample (smoke runs)")
    p.add_argument("--baseline", action="store_true", help="no key: the guideline-order baseline only")
    p.add_argument("--rescore", default=None, metavar="JSON", help="no calls: rebuild the tables of an earlier run from its records")
    args = p.parse_args(argv)
    if args.rescore:
        return rescore(args.rescore)
    sample, convs, points = load_points(args.sample, args.limit)
    lookup = {c["id"]: c for c in convs}
    arms = [a.strip() for a in args.arms.split(",") if a.strip()]
    models = [m.strip() for m in args.models.split(",") if m.strip()]
    if args.baseline:
        recs = baseline_records(points)
        groups = {("baseline", "none"): score(recs, lookup)}
        md = render(groups, sample, len(convs)).replace("# Assist", "# Assist baseline (guideline order, gold intent given)", 1)
        print(md)
        write(args.out, f"assist-baseline-{today()}", md, recs)
        return 0
    client = gate(estimate(points, arms, models), args, client, models=[model_id(m) for m in models])
    if client is None:
        return 0 if args.estimate_only else 2
    recs, partial = run_keyed(client, points, arms, models, args)
    groups = {}
    for r in recs:
        groups.setdefault((r["arm"], r["model"]), []).append(r)
    groups = {k: score(v, lookup) for k, v in groups.items()}
    md = render(groups, sample, len(convs), partial)
    print(md)
    # A --limit run is a smoke run: its own file name, never read as the headline by evals/readout_table.py.
    # A run with a non-Anthropic arm gets its own name too, so the readout keeps reading the Claude run.
    other = sorted({m for m in models if provider(model_id(m)) != "anthropic"})
    write(args.out, "assist-" + "".join(f"{m}-" for m in other) + today() + (f"-limit{args.limit}" if args.limit else "")
          + ("-partial" if partial else ""), md, recs)
    return 130 if partial else 0


if __name__ == "__main__":
    sys.exit(main())
