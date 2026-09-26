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


class FakeGemini:
    """The Google GenAI surface the Gemini path uses: models.generate_content,
    answering with the same responder shape as FakeClient."""

    def __init__(self, responder, cached=0, fail_first=0, vertexai=False):
        self.responder = responder
        self.cached = cached
        self.fail_first = fail_first
        self.vertexai = vertexai
        self.requests = []
        self.models = self
        self.caches = self
        self.created, self.deleted = [], []
        self.expire_next = 0  # the next N calls naming a cache answer 404, as an expired cache would

    def create(self, *, model, config):
        name = f"cachedContents/{len(self.created) + 1}"
        self.created.append({"model": model, "config": config, "name": name})
        return SimpleNamespace(name=name, usage_metadata=SimpleNamespace(total_token_count=28000))

    def delete(self, *, name):
        self.deleted.append(name)

    def generate_content(self, *, model, contents, config):
        self.requests.append({"model": model, "contents": contents, "config": config})
        if config.get("cached_content") and self.expire_next:
            self.expire_next -= 1
            err = RuntimeError("404 NOT_FOUND cached content")
            err.code = 404
            raise err
        if self.fail_first:
            self.fail_first -= 1
            err = RuntimeError("503 UNAVAILABLE")
            err.code = 503
            raise err
        payload = self.responder({"output_config": {"format": {"schema": config.get("response_json_schema") or {}}},
                                  "messages": [{"content": contents[0]["parts"][0]["text"]}]})
        return SimpleNamespace(text=json.dumps(payload), model_version=model,
                               candidates=[SimpleNamespace(finish_reason=SimpleNamespace(name="STOP"))],
                               usage_metadata=SimpleNamespace(prompt_token_count=30000, cached_content_token_count=self.cached,
                                                              candidates_token_count=70, thoughts_token_count=12))


class MultiClient:
    """Anthropic and Gemini stubs behind one object, as evals/common.Clients."""

    def __init__(self, anthropic, gemini):
        self.messages = anthropic
        self.gemini = gemini
