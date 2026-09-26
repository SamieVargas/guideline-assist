"""Part 11 data: the JSON the replay page on samievargas.com reads
(`/assist/`, data/assist-replay.json in that repo).

Everything in the file is copied or scored from the newest complete keyed
result files in evals/results/; nothing is typed by hand, and the page does
no arithmetic beyond formatting.

    python evals/export_viewer.py                       # Sonnet 5, arm A, six conversations
    python evals/export_viewer.py --out ../samievargas.github.io/data/assist-replay.json

Which conversations: walking assist_100 in sample order, the first
conversation of each flow that has at least three action points, until
there are --conversations of them. Which QA copies: the first perturbed copy
of each defect kind in qa_100 order, caught or not. Neither is picked for
how well the model did.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from common import RESULTS, ROOT
from assist_scoring import TRIGGERS_PER_CONVERSATION, score as score_assist
from core import samples
from core.data import by_id, load_split
from core.guidelines import library, section_id
from core.models import PRICES_READ_ON
from core.perturb import KINDS
from core.qa import qa_rules, required_steps
from readout_table import newest, records
from run_qa import build_set, score as score_qa

OUT = ROOT / "evals" / "viewer" / "replay.json"
BADGE = "ABCD, ASAPP Research, role-played conversations with trained crowdworkers, no real customers"
LICENSE = "ABCD is MIT licensed, Copyright (c) 2021 ASAPP Research"
REPO = "https://github.com/SamieVargas/guideline-assist"


def turn_row(t):
    return {"i": t["i"], "speaker": t["speaker"], "text": t["text"], "action": t["action"], "values": t["values"]}


def replay(recs, test, *, arm, model, n):
    mine = [r for r in recs if r["arm"] == arm and r["model"] == model]
    by_conv = {}
    for r in mine:
        by_conv.setdefault(r["conv"], []).append(r)
    order = samples.load("assist_100")["ids"]
    out, flows = [], set()
    for cid in order:
        pts = sorted(by_conv.get(cid, []), key=lambda r: r["i"])
        c = test[cid]
        if not pts or c["flow"] in flows or sum(p["kind"] == "action" for p in pts) < 3:
            continue
        flows.add(c["flow"])
        out.append({
            "id": cid, "subflow": c["subflow"], "flow": c["flow"],
            "section": library()[section_id(c["subflow"])]["title"],
            "turns": [turn_row(t) for t in c["turns"]],
            "points": [{"i": p["i"], "kind": p["kind"], "gold_action": p["gold_action"], "gold_values": p["gold_values"],
                        "intent": p["pred"]["intent"], "intent_ok": p["pred"]["intent"] == c["subflow"],
                        "section_id": p["pred"]["section_id"],
                        "section": library().get(p["pred"]["section_id"], {}).get("title"),
                        "next_action": p["pred"]["next_action"], "slot_values": p["pred"]["slot_values"],
                        "suggestion": p["pred"]["suggestion"], "latency_ms": p["latency_ms"],
                        "action_ok": p["pred"]["next_action"] == p["gold_action"]} for p in pts],
        })
        if len(out) == n:
            break
    return out


def qa_examples(qa_recs, model):
    _, untouched, perturbed = build_set()
    convs = {c["id"]: c for c in untouched + perturbed}
    model_by = {r["conv"]: r for r in qa_recs if r.get("model") == model}
    out = []
    for kind in KINDS:
        c = next((x for x in perturbed if x["perturbation"]["kind"] == kind and x["id"] in model_by), None)
        if c is None:
            continue
        m = model_by[c["id"]]["statuses"]
        rules = qa_rules(c)
        p = c["perturbation"]
        out.append({
            "kind": kind, "id": c["id"], "twin": c["twin"], "subflow": c["subflow"], "detail": p["detail"],
            "expected": p["expected"], "target": p["actions"],
            "caught": any(m[a]["status"] == p["expected"] for a in p["actions"]),
            "steps": [{"action": a, "model": m[a], "rules": rules[a], "planted": a in p["actions"]} for a in required_steps(c["subflow"])],
            "turns": [turn_row(t) for t in convs[c["id"]]["turns"]],
        })
    return out


def _row(recs, test, **extra) -> dict:
    s = score_assist(recs, test)
    u = [r["usage"] for r in recs]
    read = sum(x["cache_read_input_tokens"] for x in u)
    total = read + sum(x["input_tokens"] + x["cache_creation_input_tokens"] for x in u)
    return {**extra, "n_points": s["n_points"], "n_action": s["n_action"], "next_action": s["next_action"],
            "intent": s["intent"], "p50_ms": s["latency_p50"], "p95_ms": s["latency_p95"],
            "cost_per_1000": s["cost_per_1000_conversations"], "false_alarm": s["false_alarm"],
            "cache_share": round(read / total, 4) if total else 0.0}


def _results(pattern):
    files = sorted(p for p in RESULTS.glob(pattern) if "partial" not in p.name and "-limit" not in p.name)
    return files[-1] if files else None


def tuning(test, assist_file) -> dict | None:
    """Section 04: the selection rounds on tune_60 (paired against their own
    same-day full) and the held-out runs on assist_100, every model and
    library measured there, recomputed from the records."""
    from run_tuning import GATE_COST, GATE_POINTS, action_ok, gates, intent_ok, paired_delta, summarize
    dev = by_id(load_split("dev"))
    rounds, sources = [], {}
    for rnd in ("r1", "r2"):
        f = _results(f"tuning-{rnd}-tune_60-2*.json")
        if not f:
            continue
        sources[rnd] = f.name
        by = {}
        for r in records(f):
            by.setdefault(r["style"], []).append(r)
        full = summarize(by["full"], dev)
        for style, rs in by.items():
            if style == "full":
                continue
            s = summarize(rs, dev)
            d_act, d_int = paired_delta(rs, by["full"], action_ok), paired_delta(rs, by["full"], intent_ok)
            g = gates(s, full, d_act, d_int)
            rounds.append({"round": rnd, "style": style, "d_next_action": d_act, "d_intent": d_int,
                           "cost_cut": round(g["cost_cut"], 4), "gates": {k: g[k] for k in ("quality", "cost", "mechanism")}})
    held = []
    if assist_file:
        for r in [x for x in records(assist_file) if x["arm"] == "A" and "haiku" in x["model"]][:1]:
            held.append(_row([x for x in records(assist_file) if x["arm"] == "A" and x["model"] == r["model"]], test,
                             model=r["model"], library="full", cache="explicit", run="parts 3-4", file=assist_file.name))
    for rnd in ("confirm", "gemini"):
        f = _results(f"tuning-{rnd}-assist_100-2*.json")
        if not f:
            continue
        by = {}
        for r in records(f):
            by.setdefault((r["model"], r["style"]), []).append(r)
        for (model, style), rs in by.items():
            held.append(_row(rs, test, model=model, library=style, cache="explicit", run=rnd, file=f.name))
    g_imp = _results("assist-gemini-2*.json")
    if g_imp:
        held.append(_row(records(g_imp), test, model=records(g_imp)[0]["model"], library="full", cache="implicit",
                         run="gemini implicit", file=g_imp.name))
    if not held:
        return None
    return {"gate_points": GATE_POINTS, "gate_cost": GATE_COST, "selection": rounds, "selection_files": sources,
            "held_out": held}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--arm", default="A")
    p.add_argument("--model", default="claude-sonnet-5")
    p.add_argument("--conversations", type=int, default=6)
    p.add_argument("--out", default=str(OUT))
    args = p.parse_args(argv)
    files = {k: newest(k) for k in ("assist", "qa", "shadow", "injection", "intent", "qa-agreement")}
    missing = [k for k, v in files.items() if v is None]
    if missing:
        print(f"needs complete keyed result files for: {', '.join(missing)}", file=sys.stderr)
        return 2
    test = by_id(load_split("test"))
    a_recs = records(files["assist"])
    q_recs = records(files["qa"])

    groups = {}
    for r in a_recs:
        groups.setdefault((r["arm"], r["model"]), []).append(r)
    ablation = []
    for (arm, model), rs in sorted(groups.items()):
        s = score_assist(rs, test)
        ablation.append({"arm": arm, "model": model, "n_points": s["n_points"], "n_action": s["n_action"],
                         "next_action": s["next_action"], "intent": s["intent"], "p50_ms": s["latency_p50"],
                         "p95_ms": s["latency_p95"], "cost_per_1000": s["cost_per_1000_conversations"],
                         "false_alarm": s["false_alarm"], "false_alarm_early": s["false_alarm_early"]})

    qa_groups = {}
    for r in q_recs:
        qa_groups.setdefault(r.get("model", "rules"), []).append(r)
    qa_summary = {}
    for name, rs in qa_groups.items():
        s = score_qa(rs)
        qa_summary[name] = {"false_flag_conversations": s["false_flag_conversations"], "recall": s["recall"],
                            "precision": s["precision"], "n_untouched": s["n_untouched"], "n_perturbed": s["n_perturbed"]}

    shadow = records(files["shadow"])
    inj = records(files["injection"])
    intent = [r for r in records(files["intent"]) if r["model"] == args.model]
    agree = records(files["qa-agreement"])
    fixtures = {}
    for r in inj:
        fixtures.setdefault(r["fixture"], []).append(r["passed"])
    stats = {
        "shadow": {"k": sum(r["category"] == "agree" for r in shadow), "n": len(shadow)},
        "hand_labels": {"k": sum(r["model"] == r["samie"] for r in agree), "n": len(agree)},
        "injection": {"k": sum(r["passed"] for r in inj), "n": len(inj),
                      "fixtures": [{"id": k, "passed": v} for k, v in sorted(fixtures.items())]},
        "conversation_intent": {"k": sum(r["gold"] == r["pred"] for r in intent), "n": len(intent)},
    }
    samp = {name: samples.load(name)["sha256"][:12] for name in ("assist_100", "qa_100", "shadow_50", "intent_300")}
    data = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "repo": REPO, "badge": BADGE, "license": LICENSE, "prices_read_on": PRICES_READ_ON,
        "source_files": {k: v.name for k, v in files.items()}, "samples": samp,
        "arm": args.arm, "model": args.model, "triggers_per_conversation": TRIGGERS_PER_CONVERSATION,
        "stats": stats, "ablation": ablation, "tuning": tuning(test, files["assist"]), "qa": {"summary": qa_summary, "examples": qa_examples(q_recs, "claude-sonnet-5")},
        "replay": replay(a_recs, test, arm=args.arm, model=args.model, n=args.conversations),
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out} ({len(data['replay'])} conversations, {len(data['qa']['examples'])} QA copies, {out.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
