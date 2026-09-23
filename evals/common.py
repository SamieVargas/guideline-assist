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


def gate(estimate, args, client=None):
    """Print the estimate; return a client, or None to stop. Order: the
    estimate always prints first, before any key check or call."""
    print(estimate.render(), flush=True)
    if args.estimate_only:
        return None
    if client is not None:
        return client
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY is not set; nothing was called. --estimate-only prints the estimate alone.", file=sys.stderr)
        return None
    if not args.yes:
        try:
            ok = input(f"Proceed at ~${estimate.total:,.2f}? [y/N] ").strip().lower() == "y"
        except EOFError:
            ok = False
        if not ok:
            print("stopped before any call", file=sys.stderr)
            return None
    import anthropic
    return anthropic.Anthropic()


def stamp(*, n, model, sample) -> str:
    """The cell stamp every results table carries: n, model, date, sample hash."""
    h = sample["sha256"][:12] if isinstance(sample, dict) else str(sample)
    return f"n={n} · {model} · {date.today().isoformat()} · sample {h}"


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
