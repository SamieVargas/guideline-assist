"""Part 7: the hand-labeling kit, blind.

Twenty items from the Part 6 QA set: 10 untouched and 10 perturbed, from
20 different base conversations (no twin pairs, so one item cannot give the
other away), shuffled under item ids L01..L20. No key file is written: the
item-to-conversation mapping is recomputed from LABEL_SEED by the scorer,
so nothing in the kit says which items were perturbed.

    python evals/labeling/make_kit.py      # writes kit.md and labels.csv (refuses to overwrite labels.csv)

Label every row of labels.csv with the same statuses the model uses
(followed, missed, out_of_order, wrong_value, not_applicable) and the turn
it points to, before looking at any model QA output. Then run
evals/qa_agreement.py.
"""

import argparse
import csv
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from run_qa import build_set  # noqa: E402
from core.contracts import QA_STATUSES  # noqa: E402
from core.data import render_transcript  # noqa: E402
from core.guidelines import render_section, section_id  # noqa: E402
from core.qa import required_steps  # noqa: E402

LABEL_SEED = 20260928
KIT = HERE / "kit.md"
LABELS = HERE / "labels.csv"


def kit_items():
    """[(item_id, conversation)], deterministic from LABEL_SEED."""
    _, untouched, perturbed = build_set()
    rng = random.Random(LABEL_SEED)
    bases = sorted({c["id"] for c in untouched}, key=lambda x: (len(x), x))
    rng.shuffle(bases)
    un_ids, pert_bases = set(bases[:10]), bases[10:]
    by_twin = {}
    for c in perturbed:
        by_twin.setdefault(c["twin"], []).append(c)
    chosen_p = []
    for b in pert_bases:
        if len(chosen_p) == 10:
            break
        if b in by_twin:
            chosen_p.append(rng.choice(sorted(by_twin[b], key=lambda c: c["id"])))
    items = [c for c in untouched if c["id"] in un_ids] + chosen_p
    items = sorted(items, key=lambda c: c["id"])
    rng.shuffle(items)
    return [(f"L{n:02d}", c) for n, c in enumerate(items, 1)]


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--force", action="store_true", help="overwrite labels.csv (erases labels)")
    args = p.parse_args(argv)
    items = kit_items()
    out = ["# QA hand-labeling kit (20 items)", "",
           "For each item, read the guideline section and the transcript, then fill the matching rows of `labels.csv`: "
           f"one status per required step from {', '.join(QA_STATUSES)}, and the turn number it points to (blank for missed / not_applicable). "
           "Some items may contain a planted defect and some may not; the kit does not say which. Label before looking at any model QA output.", ""]
    rows = []
    for item, c in items:
        req = required_steps(c["subflow"])
        out += [f"## {item} · subflow `{c['subflow']}`", "", f"Required steps in order: {' -> '.join(req)}", "",
                "<details><summary>Guideline section</summary>", "", "```", render_section(section_id(c["subflow"])), "```", "</details>", "",
                "```", render_transcript(c["turns"]), "```", ""]
        rows += [{"item": item, "action": a, "status": "", "turn": "", "note": ""} for a in req]
    KIT.write_text("\n".join(out), encoding="utf-8")
    print(f"wrote {KIT.name} ({len(items)} items)")
    if LABELS.exists() and not args.force:
        print(f"{LABELS.name} exists; left untouched (use --force to reset it)")
        return 0
    with open(LABELS, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["item", "action", "status", "turn", "note"])
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {LABELS.name} ({len(rows)} rows to label)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
