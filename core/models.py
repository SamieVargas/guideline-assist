"""Model ids, per-model request settings and list prices, pinned in one place.

Ids and prices were read on PRICES_READ_ON from the Claude API reference
bundled with Claude Code (its model table was last refreshed 2026-06-24).
Re-check both against https://www.anthropic.com/pricing and the models
overview page before quoting any dollar figure computed from them.
"""

PRICES_READ_ON = "2026-09-23"

# The two arms of the deployment question: a Haiku-class and a Sonnet-class
# model. Haiku is pinned to its dated snapshot; Sonnet 5 has no dated
# snapshot, so its id is the alias the API documents.
MODELS = {
    "haiku": "claude-haiku-4-5-20251001",
    "sonnet": "claude-sonnet-5",
}
# A third arm from another provider, run only when named (--models gemini),
# never by default. Gemini is the Flash-class model the real-time assist
# market prices against. Its id and prices were read from search results on
# 2026-09-25 (ai.google.dev was not reachable from the build machine), so
# they are UNCONFIRMED: check both on https://ai.google.dev/gemini-api/docs/pricing
# before a keyed run, and before quoting any dollar figure computed from them.
EXTRA_MODELS = {
    "gemini": "gemini-3.8-flash",
}
PROVIDER = {"claude-haiku-4-5-20251001": "anthropic", "claude-sonnet-5": "anthropic", "gemini-3.8-flash": "google"}
DEFAULT_ASSIST = "haiku"
DEFAULT_QA = "sonnet"

# Extra request fields per model. Sonnet 5 runs adaptive thinking when the
# parameter is omitted; the assist is a latency-bound classifier, so thinking
# is turned off explicitly there. Haiku 4.5 does not think unless asked.
REQUEST_EXTRAS = {
    "claude-haiku-4-5-20251001": {},
    "claude-sonnet-5": {"thinking": {"type": "disabled"}},
    # Gemini Flash thinks by default and bills thinking as output; the lowest
    # level is the closest match to Sonnet with thinking disabled.
    "gemini-3.8-flash": {"thinking_config": {"thinking_level": "MINIMAL"}},
}

# The shortest prefix each model will cache. A shorter prefix is sent with
# cache_control and silently not cached (cache_creation_input_tokens stays 0).
CACHE_MIN_TOKENS = {
    "claude-haiku-4-5-20251001": 4096,
    "claude-sonnet-5": 1024,
    # Gemini caches implicitly: a repeated prefix is discounted when the
    # service happens to hit, with no cache_control and no write charge.
    "gemini-3.8-flash": 1024,
}

# USD per million tokens. Cache writes (5-minute TTL) bill at 1.25x input,
# cache reads at 0.1x input.
PRICES = {
    "claude-haiku-4-5-20251001": {"input": 1.00, "output": 5.00},
    "claude-sonnet-5": {"input": 2.00, "output": 10.00},
    # UNCONFIRMED (see EXTRA_MODELS). Output includes thinking tokens. The
    # cached-input price assumes the 0.1x implicit-cache discount.
    "gemini-3.8-flash": {"input": 0.75, "output": 3.75, "cache_read": 0.075},
}
CACHE_WRITE_MULT = 1.25
CACHE_READ_MULT = 0.10


def model_id(name: str) -> str:
    """Accepts a short name ("haiku") or a pinned id."""
    if name in MODELS:
        return MODELS[name]
    if name in EXTRA_MODELS:
        return EXTRA_MODELS[name]
    if name in PRICES:
        return name
    raise KeyError(f"unknown model {name!r}; use one of {sorted(MODELS) + sorted(EXTRA_MODELS)} or a pinned id in core/models.py")


def cost_usd(model: str, usage: dict) -> float:
    """Dollars for one usage record (input, cache writes, cache reads, output).
    A model with no price row raises rather than pricing it at zero."""
    if model not in PRICES:
        raise KeyError(f"no price recorded for {model!r}; add it to PRICES in core/models.py")
    p = PRICES[model]
    u = usage or {}
    return (u.get("input_tokens", 0) * p["input"]
            + u.get("cache_creation_input_tokens", 0) * p["input"] * CACHE_WRITE_MULT
            + u.get("cache_read_input_tokens", 0) * p.get("cache_read", p["input"] * CACHE_READ_MULT)
            + u.get("output_tokens", 0) * p["output"]) / 1_000_000


def provider(model: str) -> str:
    return PROVIDER.get(model, "google" if model.startswith("gemini") else "anthropic")
