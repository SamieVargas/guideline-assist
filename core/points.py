"""Where the assist is called, and what the guideline expects there.

Action points: every turn index i where the gold transcript's turn i is an
ACTION. The assist sees turns[:i]; the gold next action is turn i.

No-action points: agent utterances i (i > 0) where the agent's run of turns
from i up to the next customer turn contains no ACTION, so nothing is due
before the customer speaks again. Drawn per conversation, seeded, as many
as that conversation has action points (fewer if it has fewer candidates).
The gold there is none_yet.
"""

import random
import re

from core.data import actions_of
from core.guidelines import subflow_sections, section_id


def action_points(conv) -> list[int]:
    return [t["i"] for t in conv["turns"] if t["speaker"] == "action"]


def no_action_candidates(conv) -> list[int]:
    turns = conv["turns"]
    out = []
    for t in turns:
        i = t["i"]
        if i == 0 or t["speaker"] != "agent":
            continue
        j, clean = i, True
        while j < len(turns) and turns[j]["speaker"] != "customer":
            if turns[j]["speaker"] == "action":
                clean = False
                break
            j += 1
        if clean:
            out.append(i)
    return out


def no_action_points(conv, seed: int) -> list[int]:
    cands = no_action_candidates(conv)
    k = min(len(cands), len(action_points(conv)))
    return sorted(random.Random(f"{seed}:{conv['id']}").sample(cands, k))


def points_for(conv, seed: int) -> list[dict]:
    pts = [{"i": i, "kind": "action", "gold_action": conv["turns"][i]["action"], "gold_values": conv["turns"][i]["values"]}
           for i in action_points(conv)]
    pts += [{"i": i, "kind": "no_action", "gold_action": "none_yet", "gold_values": []} for i in no_action_points(conv, seed)]
    return sorted(pts, key=lambda p: p["i"])


def guideline_next(conv, i) -> str | None:
    """The first required step (kb.json order) not yet done before turn i,
    or None when every required step is done."""
    done = {t["action"] for t in conv["turns"][:i] if t["speaker"] == "action"}
    for a in subflow_sections()[section_id(conv["subflow"])]["required_actions"]:
        if a not in done:
            return a
    return None


def compliant(conv) -> bool:
    """Every required step appears, and their first occurrences follow the
    kb.json order: compliant as far as the gold actions show."""
    req = subflow_sections()[section_id(conv["subflow"])]["required_actions"]
    first = {}
    for t in actions_of(conv):
        first.setdefault(t["action"], t["i"])
    if any(a not in first for a in req):
        return False
    pos = [first[a] for a in req]
    return pos == sorted(pos)


def norm_value(v: str) -> str:
    v = str(v).strip().lower().replace("$", "")
    v = re.sub(r"\s+", " ", v)
    return v[:-3] if re.fullmatch(r"\d+\.00", v) else v


def values_match(pred, gold) -> bool:
    return sorted(norm_value(x) for x in (pred or [])) == sorted(norm_value(x) for x in (gold or []))


def value_recall(pred, gold) -> float | None:
    g = [norm_value(x) for x in (gold or [])]
    if not g:
        return None
    p = {norm_value(x) for x in (pred or [])}
    return sum(1 for x in g if x in p) / len(g)
