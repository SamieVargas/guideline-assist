"""The cost estimate printed before every keyed run.

No tokenizer runs offline, so input is estimated from characters. The
per-model ratios and overheads below were measured on the full Parts 3-4
run of 2026-09-24 (evals/results/assist-2026-09-24.json, 4,130 calls),
where the first-draft estimate (a flat 4 chars/token) came in at $12.63
against $19.70 actually billed:
- the two tokenizers differ: the 103,474-character library prompt is
  27,563 tokens on Haiku 4.5 and 37,708 on Sonnet 5;
- a call with no cached prefix bills ~830 (Haiku) / ~1,070 (Sonnet) input
  tokens beyond its prompt text (the structured-output schema and message
  framing); with a cached prefix that overhead is inside the cached read;
- validator retries add calls.
The high bound stays HIGH_FACTOR above the estimate.
"""

from core.models import CACHE_MIN_TOKENS, CACHE_READ_MULT, CACHE_WRITE_MULT, PRICES

CHARS_PER_TOKEN = 4.0  # fallback for a model with no measurement
HIGH_FACTOR = 1.35

# Measured 2026-09-24 (see the module docstring).
MEASURED = {
    "claude-haiku-4-5-20251001": {"chars_per_token": 3.75, "uncached_call_overhead": 830, "retry_rate": 0.06},
    "claude-sonnet-5": {"chars_per_token": 2.74, "uncached_call_overhead": 1070, "retry_rate": 0.02},
}


def tokens(chars: int, model: str | None = None) -> int:
    cpt = MEASURED.get(model, {}).get("chars_per_token", CHARS_PER_TOKEN)
    return int(chars / cpt) + 1


def call_cost(model: str, *, uncached_chars: int, cached_chars: int = 0, out_tokens: int = 150, cache_hit: bool = True) -> float:
    """One call. A cached block below the model's minimum is billed as
    ordinary input; a cached block above it is a read when cache_hit, else a
    write."""
    p = PRICES[model]
    m = MEASURED.get(model, {})
    unc, cac = tokens(uncached_chars, model), tokens(cached_chars, model) if cached_chars else 0
    if cac and cac < CACHE_MIN_TOKENS.get(model, 0):
        unc, cac = unc + cac, 0
    if not cac:
        unc += m.get("uncached_call_overhead", 0)
    cached_rate = CACHE_READ_MULT if cache_hit else CACHE_WRITE_MULT
    one = (unc * p["input"] + cac * p["input"] * cached_rate + out_tokens * p["output"]) / 1_000_000
    return one * (1 + m.get("retry_rate", 0))


class Estimate:
    def __init__(self, title: str):
        self.title = title
        self.rows = []  # (label, model, calls, usd)

    def add(self, label: str, model: str, calls: int, usd: float):
        self.rows.append((label, model, calls, usd))

    @property
    def total(self) -> float:
        return sum(r[3] for r in self.rows)

    def render(self) -> str:
        lines = [f"Cost estimate: {self.title}", f"(per-model token ratios measured 2026-09-24; high bound x{HIGH_FACTOR})"]
        for label, model, calls, usd in self.rows:
            lines.append(f"  {label:<38} {model:<28} {calls:>6} calls  ~${usd:,.2f}")
        lines.append(f"  {'TOTAL':<38} {'':<28} {sum(r[2] for r in self.rows):>6} calls  ~${self.total:,.2f} (high ${self.total * HIGH_FACTOR:,.2f})")
        return "\n".join(lines)
