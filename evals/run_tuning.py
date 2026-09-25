"""Prompt tuning for cost: arm A with the guideline library rendered at
different lengths (core.guidelines.LIBRARY_STYLES), scored against the
full rendering on the same call points. The plan, the gates and the
per-round record are in docs/prompt-tuning.md.

    python evals/run_tuning.py --estimate-only                         # round 1, what it would cost
    python evals/run_tuning.py --round r1                              # keyed: five styles on tune_60 (dev split)
    python evals/run_tuning.py --round confirm --sample assist_100 --styles full,<winner>
    python evals/run_tuning.py --round haiku --sample assist_100 --model haiku --styles full,<winner>

tune_60 is drawn from ABCD's dev split and is the only sample whose
transcripts are read while choosing changes; assist_100 (test) is scored
once, at the confirm. Every style in a run uses the same call points, so
each row's delta against `full` is paired point by point.

The response-cache tag is `tune-<round>`, so a round never reuses an
answer from an earlier round or from the Parts 3-4 run. Calls run one at
a time, style by style, so each style's cached prefix stays warm.
"""

import argparse
import math
import sys

from common import add_keyed_args, gate, today, write
from assist_scoring import TRIGGERS_PER_CONVERSATION, score
from core import samples
from core.assist import ASSIST_RULES, assist
from core.data import by_id, load_split, render_transcript
from core.estimate import Estimate, call_cost
from core.guidelines import LIBRARY_STYLES, render_library
from core.metrics import mean, pct
from core.models import model_id, provider
from core.points import points_for
from run_assist import POINT_SEED, _record

GATE_POINTS = 3.0     # quality band: next action and intent each no more than 3 points below full
GATE_COST = 0.20      # cost margin: at least 20% cheaper per turn than full


def load_points(sample_name, limit=None):
    rec = samples.load(sample_name)
    pool = by_id(load_split(rec["split"]))
    convs = [pool[i] for i in rec["ids"]][: limit or None]
    return rec, convs, [(c, p) for c in convs for p in points_for(c, POINT_SEED)]


def estimate(points, styles, model) -> Estimate:
    mid = model_id(model)
    est = Estimate(f"prompt tuning, {len(points)} call points x {len(styles)} library style(s) on {mid}")
    for style in styles:
        lib = len(ASSIST_RULES) + len(render_library(style)) + 20
        usd = sum(call_cost(mid, uncached_chars=len(render_transcript(c["turns"][: p["i"]])) + 80, cached_chars=lib,
                            out_tokens=90, cache_hit=n > 0) for n, (c, p) in enumerate(points))
        est.add(f"library {style}", mid, len(points), usd)
        if provider(mid) == "google":
            miss = sum(call_cost(mid, uncached_chars=lib + len(render_transcript(c["turns"][: p["i"]])) + 80, out_tokens=90)
                       for c, p in points)
            est.worst_extra += miss - usd
            est.notes.append(f"{style}: ~${miss:,.2f} if Gemini's implicit cache never hits")
    if provider(mid) == "google":
        est.notes.append(f"{mid} id and prices in core/models.py are unconfirmed; check them on ai.google.dev first.")
    return est


def paired_delta(recs, base, key) -> dict:
    """Mean of (style right - full right) over the call points both runs
    scored, in points, with a normal-approximation 95% interval."""
    b = {(r["conv"], r["i"]): r for r in base}
    d = [float(key(r)) - float(key(b[(r["conv"], r["i"])])) for r in recs if (r["conv"], r["i"]) in b]
    d = [x for x in d if not math.isnan(x)]
    if not d:
        return {"n": 0, "delta": None, "lo": None, "hi": None}
    m = sum(d) / len(d)
    sd = math.sqrt(sum((x - m) ** 2 for x in d) / (len(d) - 1)) if len(d) > 1 else 0.0
    half = 1.96 * sd / math.sqrt(len(d))
    return {"n": len(d), "delta": 100 * m, "lo": 100 * (m - half), "hi": 100 * (m + half)}


def action_ok(r):
    return r["pred"]["next_action"] == r["gold_action"] if r["kind"] == "action" else float("nan")


def intent_ok(r):
    return r["pred"]["intent"] == r["subflow"]


def summarize(recs, lookup) -> dict:
    s = score(recs, lookup)
    u = [r["usage"] for r in recs]
    s.update({"cache_read_mean": round(mean([x["cache_read_input_tokens"] for x in u]), 1),
              "cache_write_mean": round(mean([x["cache_creation_input_tokens"] for x in u]), 1),
              "uncached_in_mean": round(mean([x["input_tokens"] for x in u]), 1),
              "output_mean": round(mean([x["output_tokens"] for x in u]), 1),
              "cost_per_turn": mean([r["cost_usd"] for r in recs]),
              "served_models": sorted({m for r in recs for m in r.get("served_models", [])})})
    return s


def gates(s, full, d_act, d_int) -> dict:
    cut = 1 - s["cost_per_turn"] / full["cost_per_turn"] if full["cost_per_turn"] else 0.0
    quality = all(d["delta"] is not None and d["delta"] >= -GATE_POINTS for d in (d_act, d_int))
    mechanism = s["cache_read_mean"] < full["cache_read_mean"] and s["output_mean"] <= full["output_mean"] * 1.10
    return {"cost_cut": cut, "quality": quality, "cost": cut >= GATE_COST, "mechanism": mechanism,
            "all": quality and cut >= GATE_COST and mechanism}


def _d(x) -> str:
    return "n/a" if x["delta"] is None else f"{x['delta']:+.1f} [{x['lo']:+.1f}, {x['hi']:+.1f}]"


def render(rows, sample, model, rnd, n_convs, partial=False) -> str:
    head = (f"# Prompt tuning · round {rnd} · {today()} · {model} arm A · sample {sample['name']} "
            f"(`{sample['sha256'][:12]}`, {sample['split']} split, {n_convs} conversations)" + (" · PARTIAL" if partial else ""))
    lines = [head, "",
             "Each row is the same call points with the guideline library rendered at a different length. Deltas are paired against "
             "`full` point by point, in percentage points with a 95% interval. Cost per 1,000 conversations = mean cost per turn x "
             f"{TRIGGERS_PER_CONVERSATION:.2f} x 1,000.", "",
             "| Library | Next action | Δ next action vs full | Intent | Δ intent vs full | Cache reads / turn | Uncached input / turn | Output / turn "
             "| p50 / p95 latency | Cost / 1,000 conversations | Cut vs full | Gates (quality · cost · mechanism) |",
             "| --- " * 12 + "|"]
    for style, s, d_act, d_int, g in rows:
        gate_cell = "baseline" if style == "full" else " · ".join("pass" if g[k] else "fail" for k in ("quality", "cost", "mechanism"))
        lines.append(f"| {style} | {pct(s['next_action'])} | {'—' if style == 'full' else _d(d_act)} | {pct(s['intent'])} | "
                     f"{'—' if style == 'full' else _d(d_int)} | {s['cache_read_mean']:,.0f} | {s['uncached_in_mean']:,.0f} | "
                     f"{s['output_mean']:,.0f} | {s['latency_p50']:.0f} / {s['latency_p95']:.0f} ms | "
                     f"${s['cost_per_1000_conversations']:,.2f} | {'—' if style == 'full' else str(round(100 * g['cost_cut'])) + '%'} | {gate_cell} |")
    served = sorted({m for _, s, *_ in rows for m in s["served_models"]})
    lines += ["", f"Gates (registered in docs/prompt-tuning.md before round 1): quality, next action and intent each no more than "
              f"{GATE_POINTS:.0f} points below full; cost, at least {100 * GATE_COST:.0f}% cheaper per turn; mechanism, fewer cached tokens "
              "read per turn and output no more than 10% longer.",
              f"Served model(s) read from the responses: {', '.join(served) or 'none recorded (cached or stubbed responses)'}. "
              f"Stamp: n={rows[0][1]['n_points']} call points per style ({rows[0][1]['n_action']} action points) · {model} · {today()} · "
              f"sample {sample['sha256'][:12]}."]
    return "\n".join(lines)


def main(argv=None, client=None) -> int:
    p = add_keyed_args(argparse.ArgumentParser(description=__doc__.splitlines()[0]))
    p.add_argument("--round", default="r1", help="names the results file and the response-cache tag")
    p.add_argument("--sample", default="tune_60")
    p.add_argument("--model", default="sonnet")
    p.add_argument("--styles", default=",".join(LIBRARY_STYLES))
    p.add_argument("--limit", type=int, default=None, help="first N conversations of the sample (smoke runs)")
    args = p.parse_args(argv)
    styles = [s.strip() for s in args.styles.split(",") if s.strip()]
    bad = [s for s in styles if s not in LIBRARY_STYLES]
    if bad or "full" not in styles:
        print(f"styles must include full and come from {LIBRARY_STYLES}; got {styles}", file=sys.stderr)
        return 2
    styles = ["full"] + [s for s in styles if s != "full"]
    sample, convs, points = load_points(args.sample, args.limit)
    lookup = {c["id"]: c for c in convs}
    mid = model_id(args.model)
    client = gate(estimate(points, styles, args.model), args, client, models=[model_id(args.model)])
    if client is None:
        return 0 if args.estimate_only else 2
    recs, partial = [], False
    try:
        for style in styles:
            for c, pt in points:
                pred, meta = assist(client, c["turns"][: pt["i"]], arm="A", model=mid, contract=args.contract,
                                    tag=f"tune-{args.round}", use_cache=not args.no_cache, library=style)
                r = _record(c, pt, pred, meta, arm="A", model=mid)
                r.update({"style": style, "round": args.round, "served_models": meta.get("served_models", [])})
                recs.append(r)
                print(f"  {style:<8} {c['id']}@{pt['i']:<3} gold={pt['gold_action']:<18} pred={pred['next_action']:<18} "
                      f"{meta['latency_ms']:>7.0f} ms  read {meta['usage']['cache_read_input_tokens']:>6}", flush=True)
    except KeyboardInterrupt:
        print("\ninterrupted; writing the partial table", file=sys.stderr)
        partial = True
    by_style = {s: [r for r in recs if r["style"] == s] for s in styles}
    by_style = {s: v for s, v in by_style.items() if v}
    if "full" not in by_style:
        return 130
    full = summarize(by_style["full"], lookup)
    rows = []
    for style, v in by_style.items():
        s = full if style == "full" else summarize(v, lookup)
        d_act, d_int = paired_delta(v, by_style["full"], action_ok), paired_delta(v, by_style["full"], intent_ok)
        rows.append((style, s, d_act, d_int, gates(s, full, d_act, d_int)))
    md = render(rows, sample, mid, args.round, len(convs), partial)
    print(md)
    stem = f"tuning-{args.round}-{args.sample}-{today()}" + (f"-limit{args.limit}" if args.limit else "") + ("-partial" if partial else "")
    write(args.out, stem, md, recs)
    return 130 if partial else 0


if __name__ == "__main__":
    sys.exit(main())
