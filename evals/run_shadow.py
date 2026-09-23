"""Part 8: shadow agreement. The assist runs silently over the 50
conversations of shadow_50 at every point where the human agent took an
action next, and its suggestion is compared with what the human did.

Every disagreement is sorted by the guideline's own next step (the first
required step in kb.json order not yet done):
  human deviated   the assist matched the guideline, the human did not
  assist wrong     the human matched the guideline, the assist did not
  both off         neither matched the guideline step

shadow_50 is a subset of assist_100 and the calls use the same cache tag
as Part 4, so after a Part 4 run for the same arm and model this table
costs nothing new.

    python evals/run_shadow.py --baseline                 # no key: the guideline-order baseline in the assist's seat
    python evals/run_shadow.py --arm A --model haiku      # keyed
"""

import argparse
import sys

from common import add_keyed_args, gate, stamp, today, write
from core import samples
from core.assist import assist
from core.data import by_id, load_split
from core.metrics import pct, rate
from core.models import DEFAULT_ASSIST, model_id
from core.points import action_points, guideline_next, values_match
from run_assist import estimate


def classify(r):
    if r["assist"] == r["human"]:
        return "agree"
    if r["assist"] == r["expected"]:
        return "human_deviated"
    if r["human"] == r["expected"]:
        return "assist_wrong"
    return "both_off"


def render(recs, sample, model, arm) -> str:
    n = len(recs)
    named = [r for r in recs if r["assist"] == r["human"] and r["human_values"]]
    cats = {k: [r for r in recs if r["category"] == k] for k in ("human_deviated", "assist_wrong", "both_off")}
    human_on_guideline = rate(sum(r["human"] == r["expected"] for r in recs), n)
    lines = [f"# Shadow agreement · {today()} · arm {arm} · `{model}` · sample shadow_50 (`{sample['sha256'][:12]}`)", "",
             "| Measure | Result | Stamp |", "| --- | --- | --- |",
             f"| Action agreement with the human's next action | {pct(rate(sum(r['category'] == 'agree' for r in recs), n))} | {stamp(n=n, model=model, sample=sample)} |",
             f"| Slot-value agreement (action agreed, human entered values) | {pct(rate(sum(values_match(r['assist_values'], r['human_values']) for r in named), len(named)))} | {stamp(n=len(named), model=model, sample=sample)} |",
             f"| Human's action was the guideline's next step | {pct(human_on_guideline)} | {stamp(n=n, model=model, sample=sample)} |",
             f"| Disagreements: human deviated from the guideline, assist followed it | {len(cats['human_deviated'])} | |",
             f"| Disagreements: assist wrong, human followed the guideline | {len(cats['assist_wrong'])} | |",
             f"| Disagreements: neither matched the guideline step | {len(cats['both_off'])} | |", ""]
    for k, title in (("human_deviated", "Human deviated (assist right, human not)"), ("assist_wrong", "Assist wrong"), ("both_off", "Neither on the guideline step")):
        lines += [f"## {title}", "", "| Conversation @ turn | Subflow | Human did | Assist suggested | Guideline next step |", "| --- | --- | --- | --- | --- |"]
        lines += [f"| {r['conv']} @ {r['i']} | {r['subflow']} | {r['human']} | {r['assist']} | {r['expected'] or '(all required steps done)'} |" for r in cats[k]] or ["| none | | | | |"]
        lines.append("")
    return "\n".join(lines)


def main(argv=None, client=None) -> int:
    p = add_keyed_args(argparse.ArgumentParser(description=__doc__.splitlines()[0]))
    p.add_argument("--arm", default="A", choices=("A", "B"))
    p.add_argument("--model", default=DEFAULT_ASSIST)
    p.add_argument("--baseline", action="store_true")
    args = p.parse_args(argv)
    sample = samples.load("shadow_50")
    test = by_id(load_split("test"))
    convs = [test[i] for i in sample["ids"]]
    pts = [(c, {"i": i, "kind": "action"}) for c in convs for i in action_points(c)]
    mid = "guideline-order baseline" if args.baseline else model_id(args.model)
    if not args.baseline:
        client = gate(estimate(pts, [args.arm], [args.model]), args, client)
        if client is None:
            return 0 if args.estimate_only else 2
    recs = []
    for c, p_ in pts:
        i = p_["i"]
        if args.baseline:
            pred = {"next_action": guideline_next(c, i) or "none_yet", "slot_values": []}
        else:
            pred, _ = assist(client, c["turns"][:i], arm=args.arm, model=mid, contract=args.contract, use_cache=not args.no_cache)
        r = {"conv": c["id"], "subflow": c["subflow"], "i": i, "human": c["turns"][i]["action"], "human_values": c["turns"][i]["values"],
             "assist": pred["next_action"], "assist_values": pred["slot_values"], "expected": guideline_next(c, i)}
        r["category"] = classify(r)
        recs.append(r)
    md = render(recs, sample, mid, "baseline" if args.baseline else args.arm)
    print(md)
    write(args.out, f"shadow-{'baseline-' if args.baseline else ''}{today()}", md, recs)
    return 0


if __name__ == "__main__":
    sys.exit(main())
