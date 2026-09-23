"""The ABCD loader: each conversation becomes one turn stream (customer,
agent, action) with the scenario labels attached.

Two facts about the file shape this relies on, both checked on load:
- `original` and `delexed` are parallel lists of the same length, speaker by
  speaker. The original text is what the model and the viewer see; the
  delexed turn carries the labels (`targets`).
- On an action turn, `targets` is [subflow, "take_action", action name,
  slot values, -1]. On every turn `targets[0]` is the ontology subflow id.
  That id is the intent label used here, not `scenario.subflow`, which
  carries a variant suffix ("timing_4", "shirt_how_2") and, in 33 of 10,042
  conversations, a name outside the ontology ("status_questions").
"""

import gzip
import json
from functools import lru_cache
from pathlib import Path

from core.enums import ACTIONS, SUBFLOW_FLOW

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "abcd"
CONVERSATIONS = DATA / "abcd_v1.1.json.gz"
SPLITS = ("train", "dev", "test")


class DataMissing(RuntimeError):
    pass


def _raw_file(path: Path):
    if not path.exists():
        raise DataMissing(f"{path} is missing; run `python scripts/fetch_data.py` first")
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=2)
def _raw(path: str):
    return _raw_file(Path(path))


def parse_conversation(raw: dict, split: str | None = None) -> dict:
    orig, delex = raw["original"], raw["delexed"]
    if len(orig) != len(delex):
        raise ValueError(f"conversation {raw['convo_id']}: original and delexed differ in length")
    intents = {t["targets"][0] for t in delex}
    if len(intents) != 1:
        raise ValueError(f"conversation {raw['convo_id']}: more than one intent label {sorted(intents)}")
    subflow = intents.pop()
    if subflow not in SUBFLOW_FLOW:
        raise ValueError(f"conversation {raw['convo_id']}: intent {subflow!r} is not an ontology subflow")
    turns = []
    for i, ((speaker, text), d) in enumerate(zip(orig, delex)):
        if speaker != d["speaker"]:
            raise ValueError(f"conversation {raw['convo_id']} turn {i}: speakers disagree")
        turn = {"i": i, "speaker": speaker, "text": text, "action": None, "values": None}
        if speaker == "action":
            name = d["targets"][2]
            if name not in ACTIONS:
                raise ValueError(f"conversation {raw['convo_id']} turn {i}: action {name!r} is not in the ontology")
            turn["action"] = name
            turn["values"] = [str(v) for v in d["targets"][3]]
        turns.append(turn)
    return {
        "id": str(raw["convo_id"]),
        "split": split,
        "flow": SUBFLOW_FLOW[subflow],
        "subflow": subflow,
        "scenario_subflow": raw["scenario"]["subflow"],
        "scenario": raw["scenario"],
        "turns": turns,
    }


def load_split(split: str, path: Path = CONVERSATIONS) -> list[dict]:
    if split not in SPLITS:
        raise ValueError(f"split must be one of {SPLITS}")
    return [parse_conversation(c, split) for c in _raw(str(path))[split]]


def load_sample_file(path: Path = DATA / "abcd_sample.json") -> list[dict]:
    """The three-conversation sample the dataset ships, for tests with no download."""
    return [parse_conversation(c, "sample") for c in _raw_file(path)]


def by_id(conversations) -> dict:
    return {c["id"]: c for c in conversations}


def actions_of(conv: dict) -> list[dict]:
    return [t for t in conv["turns"] if t["speaker"] == "action"]


def render_turn(t: dict) -> str:
    """How one turn is shown to the model. An action turn shows the logged
    action name and its slot values next to the system text, because several
    actions (verify-identity, validate-purchase) log values their system text
    never prints, and QA cannot judge a value it cannot see."""
    if t["speaker"] == "action":
        vals = ", ".join(t["values"] or [])
        return f"[{t['i']}] ACTION {t['action']}({vals}) :: {t['text']}"
    return f"[{t['i']}] {t['speaker'].upper()}: {t['text']}"


def render_transcript(turns, include_actions: bool = True) -> str:
    return "\n".join(render_turn(t) for t in turns if include_actions or t["speaker"] != "action")
