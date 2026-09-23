"""The closed-enum contracts: what the live assist, the arm-B intent call,
the conversation-level intent call and the post-call QA may return. Every
enum is built from core/enums.py (generated from the ontology) or from the
guideline library's section ids, never typed here."""

import json

from core.enums import ACTIONS, SUBFLOWS
from core.guidelines import section_ids

UNCLEAR = "unclear"
NONE_YET = "none_yet"
NO_SECTION = "none"
QA_STATUSES = ("followed", "missed", "out_of_order", "wrong_value", "not_applicable")
QA_FLAGS = ("missed", "out_of_order", "wrong_value")  # the statuses a supervisor would act on
SUGGESTION_MAX_CHARS = 240

INTENTS = SUBFLOWS + (UNCLEAR,)
NEXT_ACTIONS = ACTIONS + (NONE_YET,)


def assist_schema(sections=None) -> dict:
    return {
        "type": "object",
        "properties": {
            "intent": {"type": "string", "enum": list(INTENTS)},
            "section_id": {"type": "string", "enum": list(sections or section_ids()) + [NO_SECTION]},
            "next_action": {"type": "string", "enum": list(NEXT_ACTIONS)},
            "slot_values": {"type": "array", "items": {"type": "string"}},
            "suggestion": {"type": "string"},
        },
        "required": ["intent", "section_id", "next_action", "slot_values", "suggestion"],
        "additionalProperties": False,
    }


def intent_schema(allow_unclear: bool = True) -> dict:
    return {
        "type": "object",
        "properties": {"intent": {"type": "string", "enum": list(INTENTS if allow_unclear else SUBFLOWS)}},
        "required": ["intent"],
        "additionalProperties": False,
    }


def qa_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "steps": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": list(ACTIONS)},
                        "status": {"type": "string", "enum": list(QA_STATUSES)},
                        "turn": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
                        "note": {"type": "string"},
                    },
                    "required": ["action", "status", "turn", "note"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["steps"],
        "additionalProperties": False,
    }


def contract_hint(example: dict) -> str:
    """Appended to the system prompt under the prompt contract, where the
    parser rather than the API holds the model to the shape."""
    return "\n\nRespond ONLY with one JSON object of this shape, no prose, no code fence:\n" + json.dumps(example)


ASSIST_EXAMPLE = {"intent": "<subflow id or unclear>", "section_id": "<flow>/<subflow> or none",
                  "next_action": "<action name or none_yet>", "slot_values": ["<value>"], "suggestion": "<one line>"}
INTENT_EXAMPLE = {"intent": "<subflow id>"}
QA_EXAMPLE = {"steps": [{"action": "<action name>", "status": "|".join(QA_STATUSES), "turn": 0, "note": "<short reason>"}]}
