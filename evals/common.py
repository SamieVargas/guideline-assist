"""Shared plumbing for the eval scripts: the keyed-run gate (estimate,
confirm, client), result stamps, and writing tables and raw records."""

import json
import os
import sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

RESULTS = ROOT / "evals" / "results"


def add_keyed_args(p):
    p.add_argument("--estimate-only", action="store_true", help="print the cost estimate and exit")
    p.add_argument("--yes", action="store_true", help="skip the confirmation after the estimate")
    p.add_argument("--contract", choices=("native", "prompt"), default="native")
    p.add_argument("--no-cache", action="store_true", help="ignore the on-disk response cache (fresh latency)")
    p.add_argument("--out", default=str(RESULTS))
    return p


class Clients:
    """One object for every provider a run needs, built lazily: `.messages`
    is the Anthropic Messages API (so existing call sites are unchanged) and
    `.gemini` the Google GenAI client, created only when a Gemini arm runs."""

    def __init__(self):
        self._anthropic = self._gemini = None

    @property
    def messages(self):
        if self._anthropic is None:
            import anthropic
            self._anthropic = anthropic.Anthropic()
        return self._anthropic.messages

    @property
    def gemini(self):
        if self._gemini is None:
            from google import genai
            # core/llm.py waits out overloads itself so the wait stays out of the latency;
            # with GOOGLE_GENAI_USE_VERTEXAI=true the SDK routes through Vertex AI (Cloud billing).
            self._gemini = genai.Client(http_options={"retry_options": {"attempts": 1}})
        return self._gemini


KEYS = {"anthropic": ("ANTHROPIC_API_KEY",), "google": ("GEMINI_API_KEY", "GOOGLE_API_KEY")}


def _vertex_ready() -> bool:
    """Vertex AI through google-genai: Application Default Credentials plus a project."""
    return os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "").lower() in ("1", "true") and bool(os.environ.get("GOOGLE_CLOUD_PROJECT"))


def gate(estimate, args, client=None, models=()):
    """Print the estimate; return a client, or None to stop. Order: the
    estimate always prints first, before any key check or call. `models`
    are the model ids the run will call; each provider among them needs
    its key (Anthropic when none are named, as before)."""
    from core.models import provider
    print(estimate.render(), flush=True)
    if args.estimate_only:
        return None
    if client is not None:
        return client
    needed = sorted({provider(m) for m in models}) or ["anthropic"]
    missing = [" or ".join(KEYS[p]) + (" (or GOOGLE_GENAI_USE_VERTEXAI=true with GOOGLE_CLOUD_PROJECT for Vertex AI)" if p == "google" else "")
               for p in needed
               if not any(os.environ.get(k) for k in KEYS[p]) and not (p == "google" and _vertex_ready())]
    if missing:
        print(f"{', '.join(missing)} is not set; nothing was called. --estimate-only prints the estimate alone.", file=sys.stderr)
        return None
    if not args.yes:
        try:
            worst = f" (up to ~${estimate.total + estimate.worst_extra:,.2f} if the cache misses)" if estimate.worst_extra else ""
            ok = input(f"Proceed at ~${estimate.total:,.2f}{worst}? [y/N] ").strip().lower() == "y"
        except EOFError:
            ok = False
        if not ok:
            print("stopped before any call", file=sys.stderr)
            return None
    return Clients()


def stamp(*, n, model, sample, on=None) -> str:
    """The cell stamp every results table carries: n, model, date, sample
    hash. `on` is the run's date when a table is rebuilt later."""
    h = sample["sha256"][:12] if isinstance(sample, dict) else str(sample)
    return f"n={n} · {model} · {on or date.today().isoformat()} · sample {h}"


def write(out_dir, stem: str, markdown: str, records) -> Path:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    md = out / f"{stem}.md"
    md.write_text(markdown.rstrip() + "\n", encoding="utf-8")
    (out / f"{stem}.json").write_text(json.dumps({"generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                                                  "records": records}, indent=1, default=str), encoding="utf-8")
    print(f"wrote {md.relative_to(ROOT) if md.is_relative_to(ROOT) else md} and .json")
    return md


def today() -> str:
    return date.today().isoformat()
