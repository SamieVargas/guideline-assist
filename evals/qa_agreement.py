"""Part 7: model QA versus Samie's hand labels on the 20-item kit.

    python evals/qa_agreement.py --records evals/results/qa-<date>.json [--model claude-sonnet-5]

Refuses to score until every row of evals/labeling/labels.csv has a
status. Reports, per step: model vs Samie (exact status agreement and
Cohen's kappa), and each of them against the labels by construction
(untouched: every step followed; perturbed: the planted status on the
planted step, followed elsewhere).
"""

import argparse
import csv
import json
import sys
from pathlib import Path

from common import stamp, today, write
from core.contracts import QA_FLAGS, QA_STATUSES
from core.metrics import cohen_kappa, pct, rate
from labeling.make_kit import LABELS, kit_items


def norm_status(s: str) -> str:
    """Hand labels are typed: "Out-of-order" and "out of order" mean out_of_order."""
    return "_".join(s.strip().lower().replace("-", " ").split())


def construction_label(conv, action):
    pert = conv.get("perturbation")
    if pert and action in pert["actions"]:
        return pert["expected"]
    return "followed"


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--records", required=True, help="the .json written by evals/run_qa.py (keyed)")
    p.add_argument("--model", default=None, help="which model's QA records to use (default: the first model in the file)")
    p.add_argument("--out", default=str(Path(__file__).resolve().parent / "results"))
    args = p.parse_args(argv)
    with open(LABELS, encoding="utf-8") as f:
        labels = list(csv.DictReader(f))
    for r in labels:
        r["status"] = norm_status(r["status"])
    blank = [r for r in labels if r["status"] not in QA_STATUSES]
    if blank:
        print(f"{len(blank)} of {len(labels)} rows in {LABELS} have no valid status yet; nothing scored.", file=sys.stderr)
        return 2
    recs = [r for r in json.loads(Path(args.records).read_text(encoding="utf-8"))["records"] if r.get("model")]
    model = args.model or (recs[0]["model"] if recs else None)
    by_conv = {r["conv"]: r for r in recs if r["model"] == model}
    items = dict(kit_items())
    rows = []
    for lab in labels:
        conv = items[lab["item"]]
        m = by_conv.get(conv["id"])
        if m is None:
            print(f"no {model} QA record for {conv['id']} (item {lab['item']}); run evals/run_qa.py first", file=sys.stderr)
            return 2
        rows.append({"item": lab["item"], "action": lab["action"], "kind": (conv.get("perturbation") or {}).get("kind", "untouched"),
                     "samie": lab["status"], "model": m["statuses"][lab["action"]]["status"],
                     "construction": construction_label(conv, lab["action"])})
    n = len(rows)
    agree = lambda a, b: rate(sum(r[a] == r[b] for r in rows), n)  # noqa: E731
    flag = lambda s: "flag" if s in QA_FLAGS else "ok"  # noqa: E731
    sample = {"sha256": "labeling-kit-seed-20260928"}
    lines = [f"# QA agreement with hand labels · {today()} · 20 items (10 untouched, 10 perturbed, blind) · model `{model}`", "",
             "| Pair | Exact status agreement (per step) | Cohen's kappa | Flag / no-flag agreement | Stamp |", "| --- | --- | --- | --- | --- |"]
    for a, b in (("model", "samie"), ("samie", "construction"), ("model", "construction")):
        fa = rate(sum(flag(r[a]) == flag(r[b]) for r in rows), n)
        lines.append(f"| {a} vs {b} | {pct(agree(a, b))} | {cohen_kappa([r[a] for r in rows], [r[b] for r in rows])} | {pct(fa)} | "
                     f"{stamp(n=n, model=model, sample=sample)} |")
    lines += ["", "| Item kind | Steps | Model vs Samie |", "| --- | --- | --- |"]
    for k in sorted({r["kind"] for r in rows}):
        rs = [r for r in rows if r["kind"] == k]
        lines.append(f"| {k} | {len(rs)} | {pct(rate(sum(r['model'] == r['samie'] for r in rs), len(rs)))} |")
    lines += ["", "Disagreements (model vs Samie):", ""]
    lines += [f"- {r['item']} {r['action']}: model {r['model']}, Samie {r['samie']}, construction {r['construction']}"
              for r in rows if r["model"] != r["samie"]] or ["- none"]
    md = "\n".join(lines)
    print(md)
    write(args.out, f"qa-agreement-{today()}", md, rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
