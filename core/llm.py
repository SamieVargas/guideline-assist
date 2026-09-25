"""One model call under a contract, with the validator in the loop.

native: the schema goes to the API as output_config.format (json_schema),
        and the parser is only a fallback.
prompt: no schema; the shape is asked for in the system prompt and the
        tolerant parser does the work.

A validation failure goes back to the model once as the next user turn with
the violations named (reject-and-retry, as in pixels-rag core/answer.py).
Latency is wall-clock around each HTTP call, summed over the attempts, so a
retry shows up in the turn's latency the way it would in production.

Responses are cached on disk under .cache/llm keyed by the full request plus
a caller tag, so rerunning a table never pays twice. A cached record keeps
the latency and usage measured when it was made and is marked from_cache;
pass use_cache=False for a fresh measurement.
"""

import hashlib
import json
import time
from pathlib import Path

from core.models import REQUEST_EXTRAS, cost_usd
from core.parse import parse_json

ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = ROOT / ".cache" / "llm"
USAGE_KEYS = ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")


def _text_of(message) -> str:
    return next((b.text for b in message.content if getattr(b, "type", "") == "text"), "")


def _usage(message) -> dict:
    u = getattr(message, "usage", None)
    return {k: int(getattr(u, k, 0) or 0) for k in USAGE_KEYS}


def _key(kwargs: dict, tag: str) -> str:
    blob = json.dumps({"request": kwargs, "tag": tag}, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _cached_create(client, kwargs, *, tag, use_cache):
    path = CACHE_DIR / f"{_key(kwargs, tag)}.json"
    if use_cache and path.exists():
        rec = json.loads(path.read_text(encoding="utf-8"))
        rec["from_cache"] = True
        return rec
    t0 = time.perf_counter()
    msg = client.messages.create(**kwargs)
    rec = {"text": _text_of(msg), "stop_reason": getattr(msg, "stop_reason", None), "usage": _usage(msg),
           "served_model": getattr(msg, "model", None),
           "latency_ms": round((time.perf_counter() - t0) * 1000, 1), "from_cache": False}
    if use_cache:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(rec), encoding="utf-8")
    return rec


def system_blocks(static: str, cached_tail: str | None = None, dynamic: str | None = None) -> list:
    """The system prompt as blocks: static instructions, then an optional
    large block marked for caching (the guideline library in arm A), then an
    optional uncached block. Instructions sit first so the cached prefix is
    byte-identical on every call."""
    blocks = [{"type": "text", "text": static}]
    if cached_tail:
        blocks[-1] = {"type": "text", "text": static + "\n\n" + cached_tail, "cache_control": {"type": "ephemeral"}}
    if dynamic:
        blocks.append({"type": "text", "text": dynamic})
    return blocks


def call(client, *, model: str, system, user: str, schema: dict, validator, contract: str = "native",
         hint: str = "", max_tokens: int = 400, max_retries: int = 1, tag: str = "run0", use_cache: bool = True,
         coerce=None) -> tuple[dict | None, dict]:
    """Returns (value, meta). value is the last parsed output (coerced), or
    None if nothing parsed; meta.valid says whether it passed the validator."""
    if contract not in ("native", "prompt"):
        raise ValueError("contract must be native or prompt")
    if contract == "prompt" and hint:
        if isinstance(system, str):
            system = system + hint
        else:
            system = list(system) + [{"type": "text", "text": hint.strip()}]
    messages = [{"role": "user", "content": user}]
    meta = {"model": model, "contract": contract, "retries": 0, "parse_path": None, "latency_ms": 0.0,
            "attempt_latency_ms": [], "usage": {k: 0 for k in USAGE_KEYS}, "violations": [], "first_violations": [],
            "valid": False, "from_cache": False, "first_value": None, "served_model": None}
    value = None
    for attempt in range(max_retries + 1):
        kwargs = {"model": model, "max_tokens": max_tokens, "system": system, "messages": messages, **REQUEST_EXTRAS.get(model, {})}
        if contract == "native":
            kwargs["output_config"] = {"format": {"type": "json_schema", "schema": schema}}
        rec = _cached_create(client, kwargs, tag=tag, use_cache=use_cache)
        meta["from_cache"] = meta["from_cache"] or rec["from_cache"]
        meta["served_model"] = rec.get("served_model")
        meta["latency_ms"] = round(meta["latency_ms"] + rec["latency_ms"], 1)
        meta["attempt_latency_ms"].append(rec["latency_ms"])
        for k in USAGE_KEYS:
            meta["usage"][k] += rec["usage"].get(k, 0)
        parsed = parse_json(rec["text"], rec["stop_reason"])
        meta["parse_path"] = parsed["path"]
        if parsed["ok"] and isinstance(parsed["value"], dict):
            value = coerce(parsed["value"]) if coerce else parsed["value"]
            violations = validator(value)
        else:
            value = None
            violations = [f"reply could not be parsed: {parsed.get('error', 'not a JSON object')}"]
        if attempt == 0:
            meta["first_violations"] = violations
            meta["first_value"] = value
        meta["violations"] = violations
        if not violations:
            meta["valid"] = True
            break
        if attempt < max_retries:
            meta["retries"] += 1
            messages = messages + [
                {"role": "assistant", "content": rec["text"] or "{}"},
                {"role": "user", "content": "Your reply failed validation:\n" + "\n".join(f"- {x}" for x in violations)
                 + "\nReturn a corrected reply under the same contract."},
            ]
    meta["cost_usd"] = round(cost_usd(model, meta["usage"]), 8)
    return value, meta
