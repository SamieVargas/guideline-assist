"""Part 1 ingest report: conversations per split, turns, actions per
conversation, subflows present in each frozen test sample, and the
guideline-library facts later tables lean on. Offline, no key.

    python evals/ingest.py
"""

import argparse
import sys
from collections import Counter

from common import RESULTS, today, write
from core import samples
from core.data import SPLITS, actions_of, by_id, load_split
from core.enums import ACTIONS, SUBFLOWS
from core.estimate import tokens
from core.guidelines import render_library, render_section, section_id, subflow_sections
from core.metrics import mean, pct, rate
from core.points import action_points, compliant, no_action_candidates


def split_row(name, convs):
    turns = [len(c["turns"]) for c in convs]
    acts = [len(actions_of(c)) for c in convs]
    agent = [sum(1 for t in c["turns"] if t["speaker"] == "agent") for c in convs]
    return (f"| {name} | {len(convs)} | {sum(turns):,} | {mean(turns):.1f} | {mean(agent):.1f} | {sum(acts):,} | {mean(acts):.2f} | {min(acts)}–{max(acts)} | "
            f"{len({c['subflow'] for c in convs})} |")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--out", default=str(RESULTS))
    args = p.parse_args(argv)
    data = {s: load_split(s) for s in SPLITS}
    test = by_id(data["test"])
    secs = subflow_sections()
    lines = [f"# Ingest · {today()} · ABCD v1.1 (asappresearch/abcd @ 6b8700c)", "",
             "Original (not delexicalized) turns. Intent label = the ontology subflow in every delexed turn's `targets[0]`.", "",
             "| Split | Conversations | Turns | Turns / conv | Agent turns / conv | Actions | Actions / conv | Min–max | Subflows |",
             "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    lines += [split_row(s, data[s]) for s in SPLITS]
    # guideline facts
    lib_chars = len(render_library())
    sec_chars = [len(render_section(s)) for s in secs]
    gold_listed = gold_required = total = 0
    for c in data["test"]:
        sec = secs[section_id(c["subflow"])]
        for t in actions_of(c):
            total += 1
            gold_listed += t["action"] in sec["listed_actions"]
            gold_required += t["action"] in sec["required_actions"]
    comp = [c for c in data["test"] if compliant(c)]
    unusual = Counter(c["scenario_subflow"] for s in SPLITS for c in data[s]
                      if not (c["scenario_subflow"] == c["subflow"] or c["scenario_subflow"].startswith(c["subflow"] + "_")))
    lines += ["", "## Guideline library and enums", "",
              "| Measure | Value |", "| --- | --- |",
              f"| Subflow ids (enum, from ontology.json) | {len(SUBFLOWS)} |",
              f"| Action names (enum, from ontology.json) | {len(ACTIONS)} |",
              f"| Sections | {len(secs)} subflow sections + 10 flow sections |",
              f"| Full library, rendered | {lib_chars:,} chars (~{tokens(lib_chars):,} tokens est.) |",
              f"| One subflow section, rendered | mean {mean(sec_chars):,.0f} chars, max {max(sec_chars):,} |",
              f"| Test gold actions the conversation's section lists | {pct(rate(gold_listed, total))} |",
              f"| Test gold actions in the section's required sequence (kb.json) | {pct(rate(gold_required, total))} |",
              f"| Test conversations compliant as far as gold actions show (every required step, in order) | {pct(rate(len(comp), len(data['test'])))} |",
              f"| Conversations whose scenario.subflow is not `<intent>` or `<intent>_<variant>` | {sum(unusual.values())} ({', '.join(f'{k}: {v}' for k, v in unusual.most_common())}) |",
              "",
              "A gold action the section does not list cannot pass the validator's listed-action rule, so the share above that is not 100% is a ceiling on validated next-action accuracy, reported rather than hidden.",
              ]
    # samples
    lines += ["", "## Frozen test samples", "", "| Sample | n | Seed | sha256 | Subflows present | Action points | No-action candidates |", "| --- | --- | --- | --- | --- | --- | --- |"]
    per_sample = {}
    for name in ("assist_100", "intent_300", "qa_100", "shadow_50"):
        try:
            rec = samples.load(name)
        except FileNotFoundError:
            lines.append(f"| {name} | not drawn yet (run evals/freeze_samples.py) | | | | | |")
            continue
        convs = [test[i] for i in rec["ids"]]
        subs = Counter(c["subflow"] for c in convs)
        per_sample[name] = subs
        lines.append(f"| {name} | {rec['n']} | {rec['seed']} | `{rec['sha256'][:12]}` | {len(subs)} of 55 | "
                     f"{sum(len(action_points(c)) for c in convs)} | {sum(len(no_action_candidates(c)) for c in convs)} |")
    if "assist_100" in per_sample:
        subs = per_sample["assist_100"]
        lines += ["", "Subflows in assist_100 (count): " + ", ".join(f"{k} {v}" for k, v in sorted(subs.items()))]
        missing = [s for s in SUBFLOWS if s not in subs]
        lines += ["", f"Absent from assist_100: {', '.join(missing) if missing else 'none'}"]
    write(args.out, f"ingest-{today()}", "\n".join(lines), {"splits": {s: len(data[s]) for s in SPLITS}})
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
