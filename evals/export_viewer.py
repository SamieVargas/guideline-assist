"""Part 11 data: the JSON the replay viewer on samievargas.com plays.

The page itself belongs in the samievargas.com repo on its own PR, after
the eval tables exist; this writes only the data it reads, from the newest
complete keyed assist and QA result files.

    python evals/export_viewer.py --arm A --model claude-haiku-4-5-20251001 --conversations 5
"""

import argparse
import json
import sys

from common import ROOT
from core.data import by_id, load_split
from core.guidelines import library
from readout_table import newest, records
from run_qa import build_set

OUT = ROOT / "evals" / "viewer" / "replay.json"
BADGE = "ABCD, ASAPP Research, role-played conversations with trained crowdworkers, no real customers"
LICENSE = "ABCD is MIT licensed (Copyright (c) 2021 ASAPP Research)"


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--arm", default="A")
    p.add_argument("--model", default="claude-haiku-4-5-20251001")
    p.add_argument("--conversations", type=int, default=5)
    args = p.parse_args(argv)
    a, q = newest("assist"), newest("qa")
    if not a or not q:
        print("needs a complete keyed assist run and a keyed QA run in evals/results/ first", file=sys.stderr)
        return 2
    test = by_id(load_split("test"))
    recs = [r for r in records(a) if r["arm"] == args.arm and r["model"] == args.model]
    convs = list(dict.fromkeys(r["conv"] for r in recs))[: args.conversations]
    replay = []
    for cid in convs:
        panel = {r["i"]: {"intent": r["pred"]["intent"], "next_action": r["pred"]["next_action"], "slot_values": r["pred"]["slot_values"],
                          "section_id": r["pred"]["section_id"], "section_title": library().get(r["pred"]["section_id"], {}).get("title"),
                          "suggestion": r["pred"]["suggestion"], "latency_ms": r["latency_ms"], "gold_action": r["gold_action"],
                          "gold_values": r["gold_values"]} for r in recs if r["conv"] == cid}
        c = test[cid]
        replay.append({"id": cid, "subflow": c["subflow"], "turns": c["turns"], "assist": panel})
    _, _, perturbed = build_set()
    qa_recs = [r for r in records(q) if r.get("model")]
    qa_by = {r["conv"]: r for r in qa_recs}
    pick = next((c for c in perturbed if c["id"] in qa_by), None)
    qa_tab = None
    if pick:
        r = qa_by[pick["id"]]
        qa_tab = {"id": pick["id"], "twin": pick["twin"], "subflow": pick["subflow"], "turns": pick["turns"],
                  "defect": pick["perturbation"], "model": r["model"], "steps": r["statuses"],
                  "caught": any(r["statuses"][x]["status"] == pick["perturbation"]["expected"] for x in pick["perturbation"]["actions"])}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"badge": BADGE, "license": LICENSE, "source_files": [a.name, q.name], "arm": args.arm,
                               "model": args.model, "replay": replay, "qa": qa_tab}, indent=1), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
