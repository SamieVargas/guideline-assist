"""Part 10: the table of measured numbers for docs/deployment-readout.md.

Reads the newest complete (not -partial, not a --limit smoke run) keyed result file of each kind in
evals/results/, recomputes the headline numbers from the raw records, and
writes docs/readout-numbers.md. A part with no keyed run yet says so; the
offline baselines are shown beside the model rows so each number has its
floor next to it. The prose of the readout is Samie's; this only builds
the numbers.

    python evals/readout_table.py
"""

import json
import sys
from pathlib import Path

from common import ROOT, RESULTS, today
from assist_scoring import TRIGGERS_PER_CONVERSATION, score as score_assist
from core.metrics import pct
from run_qa import score as score_qa

OUT = ROOT / "docs" / "readout-numbers.md"


def newest(prefix: str, baseline=False):
    pat = f"{prefix}-baseline-*.json" if baseline else f"{prefix}-2*.json"
    files = sorted(p for p in RESULTS.glob(pat) if "partial" not in p.name and "-limit" not in p.name)
    return files[-1] if files else None


def records(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))["records"] if path else None


def main() -> int:
    rows = ["| Readout metric | Source | Measured | File |", "| --- | --- | --- | --- |"]

    def add(metric, source, value, path):
        rows.append(f"| {metric} | {source} | {value} | {Path(path).name if path else 'not run yet'} |")

    from core.data import by_id, load_split
    test = by_id(load_split("test"))
    a = newest("assist")
    if a:
        groups = {}
        for r in records(a):
            groups.setdefault((r["arm"], r["model"]), []).append(r)
        for (arm, model), recs in groups.items():
            s = score_assist(recs, test)
            tag = f"arm {arm} · {model} · n={s['n_points']}"
            add("Adherence: next action = gold next action", tag, pct(s["next_action"]), a)
            add("Time to correct intent (turn index, median; never)", tag, f"{s['turns_to_stable']['median']}; never {s['turns_to_stable']['never']}/{s['turns_to_stable']['n']}", a)
            add("Latency budget: p50 / p95 per turn", tag, f"{s['latency_p50']:.0f} / {s['latency_p95']:.0f} ms", a)
            add("False suggestions when nothing is due (of which early: the agent's next action)", tag,
                f"{pct(s['false_alarm'])} ({pct(s['false_alarm_early'])})", a)
            add("Cost per 1,000 conversations", tag, f"${s['cost_per_1000_conversations']:,.2f} ({TRIGGERS_PER_CONVERSATION:.2f} triggers/conv)", a)
    else:
        add("Adherence, time to intent, latency, cost", "Parts 3–4", "not run yet", None)
    b = newest("assist", baseline=True)
    if b:
        s = score_assist(records(b), test)
        add("Floor: guideline-order baseline, gold intent given", f"no model · n={s['n_points']}", f"next action {pct(s['next_action'])}", b)

    sh = newest("shadow")
    if sh:
        recs = records(sh)
        n = len(recs)
        agree = sum(r["category"] == "agree" for r in recs)
        add("Suggestion acceptance proxy: shadow action agreement", f"n={n}", f"{agree}/{n} ({agree / n * 100:.1f}%)", sh)
        add("Human deviated / assist wrong / both off", f"n={n}",
            " / ".join(str(sum(r["category"] == k for r in recs)) for k in ("human_deviated", "assist_wrong", "both_off")), sh)
    else:
        add("Suggestion acceptance proxy (shadow agreement)", "Part 8", "not run yet", None)

    q = newest("qa")
    if q:
        groups = {}
        for r in records(q):
            groups.setdefault(r.get("model", "rules (no model)"), []).append(r)
        for model, recs in groups.items():
            s = score_qa(recs)
            add("QA false-flag rate on untouched conversations", f"{model} · n={s['n_untouched']}", pct(s["false_flag_conversations"]), q)
            add("QA recall remove / swap / value", model, " / ".join(pct(s["recall"][k]) for k in ("remove", "swap", "value")), q)
    else:
        qb = newest("qa", baseline=True)
        if qb:
            s = score_qa(records(qb))
            add("QA false-flag rate (rules, no model)", f"n={s['n_untouched']}", pct(s["false_flag_conversations"]), qb)
        add("QA false-flag rate (model)", "Part 6", "not run yet", None)

    ag = newest("qa-agreement")
    if ag:
        add("QA agreement with Samie's 20", "Part 7", "see file", ag)
    else:
        import csv
        from labeling.make_kit import LABELS
        with open(LABELS, encoding="utf-8") as f:
            done = all(r["status"].strip() for r in csv.DictReader(f))
        add("QA agreement with Samie's 20", "Part 7", "labels done; needs a keyed QA run" if done else "not labeled yet", None)
    inj = newest("injection")
    if inj:
        recs = records(inj)
        add("Injection: runs matching the clean twin", f"n={len(recs)}", pct(sum(r["passed"] for r in recs) / len(recs)), inj)
    else:
        add("Injection resistance", "Part 9", "not run yet", None)
    it = newest("intent")
    if it:
        from run_intent import score as score_intent
        groups = {}
        for r in records(it):
            groups.setdefault(r["model"], []).append(r)
        for model, recs in groups.items():
            s = score_intent(recs)
            add("Conversation intent accuracy / macro-F1", f"{model} · n={s['n']}", f"{pct(s['accuracy'])} / {s['macro_f1']}", it)
    else:
        add("Conversation intent", "Part 5", "not run yet", None)

    md = "\n".join([f"# Measured numbers for the deployment readout · built {today()}", "",
                    "Generated by `evals/readout_table.py` from the newest complete result files. Do not edit by hand; rerun it.",
                    "Handle time, resolution and CSAT are not measurable on this dataset and have no row.", ""] + rows) + "\n"
    OUT.write_text(md, encoding="utf-8")
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
