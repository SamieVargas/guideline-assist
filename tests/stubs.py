"""A scripted Anthropic client for the offline tests (after pixels-rag
tests/stubs.py): each call pops the next reply, or asks a responder
function, and every request is kept so a test can look at what was sent."""

import json
from types import SimpleNamespace


def reply(payload, stop_reason="end_turn", cache_read=0, cache_write=0):
    text = payload if isinstance(payload, str) else json.dumps(payload)
    return SimpleNamespace(content=[SimpleNamespace(type="text", text=text)], stop_reason=stop_reason,
                           usage=SimpleNamespace(input_tokens=120, output_tokens=60, cache_read_input_tokens=cache_read,
                                                 cache_creation_input_tokens=cache_write))


class FakeClient:
    def __init__(self, replies=(), responder=None):
        self.replies = list(replies)
        self.responder = responder
        self.requests = []
        self.messages = self

    def create(self, **kwargs):
        self.requests.append(kwargs)
        if self.responder is not None:
            r = self.responder(kwargs)
        elif self.replies:
            r = self.replies.pop(0)
        else:
            raise AssertionError("the stub client was asked for more replies than it was given")
        return r if hasattr(r, "content") else reply(r)


def assist_out(intent, action, values=(), section=None, suggestion="Ask for the customer's full name."):
    from core.contracts import NO_SECTION, UNCLEAR
    from core.guidelines import section_id
    sid = section if section is not None else (NO_SECTION if intent == UNCLEAR else section_id(intent))
    return {"intent": intent, "section_id": sid, "next_action": action, "slot_values": list(values), "suggestion": suggestion}
