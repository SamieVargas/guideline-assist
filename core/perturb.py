"""Perturbed copies for the QA test set, each with exactly one known defect
and a pointer to its untouched twin. All choices come from a seeded RNG
keyed on the conversation id and the defect kind, so a copy is the same on
every machine.

remove  one required step's ACTION turns are deleted, with the agent line
        right before its first occurrence (the line that announced it).
        Expected: that step is `missed`.
swap    two required steps adjacent in the guideline order, each logged
        exactly once, trade places. Expected: `out_of_order` on either.
value   one slot value that the customer typed in the chat is changed in
        the ACTION turn (log and system text). Expected: `wrong_value`.
"""

import copy
import json
import random
import re
from pathlib import Path

from core.guidelines import section_id, subflow_sections
from core.points import norm_value

ROOT = Path(__file__).resolve().parent.parent
KINDS = ("remove", "swap", "value")
EXPECTED = {"remove": "missed", "swap": "out_of_order", "value": "wrong_value"}


def _enumerables() -> dict:
    o = json.loads((ROOT / "data" / "abcd" / "ontology.json").read_text(encoding="utf-8"))
    return {k: [str(x).lower() for x in v] for k, v in o["values"]["enumerable"].items()}


def _required(conv):
    return subflow_sections()[section_id(conv["subflow"])]["required_actions"]


def _renumber(conv, turns, kind, target, detail):
    new = copy.deepcopy(conv)
    new["turns"] = [{**t, "i": n} for n, t in enumerate(turns)]
    new["id"] = f"{conv['id']}~{kind}"
    new["twin"] = conv["id"]
    new["perturbation"] = {"kind": kind, "actions": target, "expected": EXPECTED[kind], "detail": detail}
    return new


def perturb_remove(conv, rng):
    req = _required(conv)
    present = [a for a in req if any(t["action"] == a for t in conv["turns"])]
    if not present:
        return None
    a = rng.choice(present)
    first = next(t["i"] for t in conv["turns"] if t["action"] == a)
    drop = {t["i"] for t in conv["turns"] if t["action"] == a}
    if first > 0 and conv["turns"][first - 1]["speaker"] == "agent":
        drop.add(first - 1)
    turns = [t for t in conv["turns"] if t["i"] not in drop]
    return _renumber(conv, turns, "remove", [a], f"removed {a} ({len(drop)} turns)")


def perturb_swap(conv, rng):
    req = _required(conv)
    count = {a: sum(1 for t in conv["turns"] if t["action"] == a) for a in req}
    pairs = [(a, b) for a, b in zip(req, req[1:]) if count[a] == 1 and count[b] == 1]
    pairs = [(a, b) for a, b in pairs
             if next(t["i"] for t in conv["turns"] if t["action"] == a) < next(t["i"] for t in conv["turns"] if t["action"] == b)]
    if not pairs:
        return None
    a, b = rng.choice(pairs)
    turns = list(conv["turns"])
    ia = next(n for n, t in enumerate(turns) if t["action"] == a)
    ib = next(n for n, t in enumerate(turns) if t["action"] == b)
    turns[ia], turns[ib] = turns[ib], turns[ia]
    return _renumber(conv, turns, "swap", [a, b], f"swapped {a} and {b}")


def _mutate(v: str, rng, enums) -> str | None:
    lv = v.lower()
    for values in enums.values():
        if lv in values and len(values) > 1:
            return rng.choice([x for x in values if x != lv])
    if re.fullmatch(r"\d{1,4}(\.\d+)?", v):
        n = float(v)
        m = n + rng.choice([-20, -10, 15, 30, 45])
        m = m if m > 0 else n + 25
        return str(int(m)) if m == int(m) else f"{m:.2f}"
    if "@" in v:
        local, _, dom = v.partition("@")
        return (local[:-1] + ("x" if local[-1:] != "x" else "q")) + "@" + dom
    if re.fullmatch(r"[a-z0-9]{5,}", lv):
        chars = list(v)
        for pos in rng.sample(range(len(chars)), 2):
            pool = "0123456789" if chars[pos].isdigit() else "abcdefghjkmnpqrstuvwxyz"
            chars[pos] = rng.choice([c for c in pool if c != chars[pos].lower()])
        return "".join(chars)
    return None


def perturb_value(conv, rng):
    req = set(_required(conv))
    said = " \n ".join(t["text"].lower() for t in conv["turns"] if t["speaker"] == "customer")
    enums = _enumerables()
    cands = []
    for t in conv["turns"]:
        if t["speaker"] != "action" or t["action"] not in req:
            continue
        for k, v in enumerate(t["values"] or []):
            if len(norm_value(v)) >= 3 and norm_value(v) in said:
                cands.append((t["i"], k, v))
    rng.shuffle(cands)
    for i, k, v in cands:
        new_v = _mutate(v, rng, enums)
        if not new_v or norm_value(new_v) == norm_value(v) or norm_value(new_v) in said:
            continue
        turns = copy.deepcopy(conv["turns"])
        t = turns[i]
        t["values"][k] = new_v
        t["text"] = re.sub(re.escape(v), lambda m: _match_case(m.group(0), new_v), t["text"], flags=re.IGNORECASE)
        return _renumber(conv, turns, "value", [t["action"]], f"{t['action']} value {v!r} -> {new_v!r}")
    return None


def _match_case(original: str, new: str) -> str:
    """Keep the system text's casing so the edit is not visible by case alone."""
    if original.isupper():
        return new.upper()
    if original.istitle():
        return new.title()
    return new


PERTURBERS = {"remove": perturb_remove, "swap": perturb_swap, "value": perturb_value}


def perturb(conv, kind: str, seed: int):
    return PERTURBERS[kind](conv, random.Random(f"{seed}:{conv['id']}:{kind}"))
