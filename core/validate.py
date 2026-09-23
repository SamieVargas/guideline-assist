"""The contracts enforced in code. The schema asks for closed enums; this
checks them again (the prompt contract has no schema behind it) and checks
what a schema cannot: that a cited section exists and belongs to the
intent, that the section lists the suggested action, and that a QA step
points at a turn that actually holds that action.

Each function returns a list of violations; empty means the output stands.
Pattern ported from pixels-rag core/validate.py (citations enforced in
code, one reject-and-retry in the caller)."""

from core.contracts import (INTENTS, NEXT_ACTIONS, NO_SECTION, NONE_YET, QA_STATUSES, SUGGESTION_MAX_CHARS,
                            UNCLEAR)
from core.enums import ACTIONS
from core.guidelines import library, section_id, subflow_sections


def validate_assist(out: dict, *, allowed_sections=None) -> list[str]:
    """allowed_sections: the section ids the model was shown (arm B shows
    one); None means the whole library (arm A)."""
    v = []
    intent, sid, action = out.get("intent"), out.get("section_id"), out.get("next_action")
    values, suggestion = out.get("slot_values"), out.get("suggestion")
    if intent not in INTENTS:
        v.append(f"intent {intent!r} is not a subflow id or {UNCLEAR!r}")
    if action not in NEXT_ACTIONS:
        v.append(f"next_action {action!r} is not an action name or {NONE_YET!r}")
    sections = subflow_sections()
    if intent == UNCLEAR:
        if sid != NO_SECTION:
            v.append(f"intent is unclear, so section_id must be {NO_SECTION!r}, not {sid!r}")
        if action != NONE_YET:
            v.append(f"intent is unclear, so next_action must be {NONE_YET!r}, not {action!r}")
    else:
        if sid not in sections:
            v.append(f"section_id {sid!r} does not exist in the guideline library")
        elif intent in INTENTS and sid != section_id(intent):
            v.append(f"section_id {sid!r} is not the section for intent {intent!r} ({section_id(intent)})")
        if allowed_sections is not None and sid not in allowed_sections and sid in sections:
            v.append(f"section_id {sid!r} was not among the sections provided")
        if sid in sections and action in ACTIONS and action not in sections[sid]["listed_actions"]:
            v.append(f"next_action {action!r} is not listed in section {sid} (it lists {', '.join(sections[sid]['listed_actions'])})")
    if not isinstance(values, list) or not all(isinstance(x, str) for x in values):
        v.append("slot_values must be a list of strings")
    elif action == NONE_YET and values:
        v.append("slot_values must be empty when next_action is none_yet")
    if not isinstance(suggestion, str) or not suggestion.strip():
        v.append("suggestion is empty")
    elif "\n" in suggestion.strip() or len(suggestion) > SUGGESTION_MAX_CHARS:
        v.append(f"suggestion must be one line under {SUGGESTION_MAX_CHARS} characters")
    return v


def citation_valid(out: dict, violations=None) -> bool:
    """The citation half of the contract only: the section exists, matches
    the intent and lists the action (or the intent is unclear with no section)."""
    violations = validate_assist(out) if violations is None else violations
    return not any(("section" in x) for x in violations)


def validate_intent(out: dict, *, allow_unclear=True) -> list[str]:
    ok = INTENTS if allow_unclear else tuple(i for i in INTENTS if i != UNCLEAR)
    return [] if out.get("intent") in ok else [f"intent {out.get('intent')!r} is not one of the allowed subflow ids"]


def validate_qa(out: dict, *, turns, required_actions) -> list[str]:
    """One entry per required step, each status in the enum, and every
    followed / out_of_order / wrong_value entry pointing at a turn that holds
    that action."""
    v = []
    steps = out.get("steps")
    if not isinstance(steps, list):
        return ["steps must be a list"]
    by_index = {t["i"]: t for t in turns}
    seen = {}
    for n, s in enumerate(steps, 1):
        a, status, turn = s.get("action"), s.get("status"), s.get("turn")
        if a not in required_actions:
            v.append(f"step {n}: {a!r} is not a required step of this subflow ({', '.join(required_actions)})")
            continue
        seen[a] = seen.get(a, 0) + 1
        if status not in QA_STATUSES:
            v.append(f"step {n} ({a}): status {status!r} is not one of {', '.join(QA_STATUSES)}")
        if status in ("followed", "out_of_order", "wrong_value"):
            t = by_index.get(turn) if isinstance(turn, int) else None
            if t is None:
                v.append(f"step {n} ({a}): status {status} must point at a turn in the transcript, got {turn!r}")
            elif t["speaker"] != "action" or t["action"] != a:
                v.append(f"step {n} ({a}): turn {turn} is not an ACTION {a} turn")
    for a in required_actions:
        if seen.get(a, 0) != 1:
            v.append(f"required step {a} appears {seen.get(a, 0)} times; it must appear exactly once")
    return v


def known_section(sid: str) -> bool:
    return sid in library()
