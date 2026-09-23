"""The cost estimate printed before every keyed run.

No tokenizer runs offline, so input is estimated at CHARS_PER_TOKEN
characters per token and shown with a high bound HIGH_FACTOR above it. The
first keyed run records real token counts; after that, trust those.
"""

from core.models import CACHE_MIN_TOKENS, CACHE_READ_MULT, CACHE_WRITE_MULT, PRICES

CHARS_PER_TOKEN = 4.0
HIGH_FACTOR = 1.35


def tokens(chars: int) -> int:
    return int(chars / CHARS_PER_TOKEN) + 1


def call_cost(model: str, *, uncached_chars: int, cached_chars: int = 0, out_tokens: int = 150, cache_hit: bool = True) -> float:
    """One call. A cached block below the model's minimum is billed as
    ordinary input; a cached block above it is a read when cache_hit, else a
    write."""
    p = PRICES[model]
    unc, cac = tokens(uncached_chars), tokens(cached_chars) if cached_chars else 0
    if cac and cac < CACHE_MIN_TOKENS.get(model, 0):
        unc, cac = unc + cac, 0
    cached_rate = CACHE_READ_MULT if cache_hit else CACHE_WRITE_MULT
    return (unc * p["input"] + cac * p["input"] * cached_rate + out_tokens * p["output"]) / 1_000_000


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
        lines = [f"Cost estimate: {self.title}", f"(input at ~{CHARS_PER_TOKEN:g} chars/token; high bound x{HIGH_FACTOR})"]
        for label, model, calls, usd in self.rows:
            lines.append(f"  {label:<38} {model:<28} {calls:>6} calls  ~${usd:,.2f}")
        lines.append(f"  {'TOTAL':<38} {'':<28} {sum(r[2] for r in self.rows):>6} calls  ~${self.total:,.2f} (high ${self.total * HIGH_FACTOR:,.2f})")
        return "\n".join(lines)
