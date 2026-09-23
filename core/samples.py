"""Frozen samples: drawn once with a recorded seed, written to
data/samples/<name>.json with the sha256 of their ids, and verified on every
load. Redrawing an existing sample needs --force and is visible in git."""

import hashlib
import json
import random
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "data" / "samples"


def ids_hash(ids) -> str:
    return hashlib.sha256("\n".join(ids).encode("utf-8")).hexdigest()


def draw(name: str, pool_ids, *, n: int, seed: int, split: str, note: str = "", force: bool = False) -> dict:
    path = SAMPLES / f"{name}.json"
    if path.exists() and not force:
        raise FileExistsError(f"{path} already exists; samples are drawn once (use --force to redraw on purpose)")
    pool = sorted(pool_ids, key=lambda x: (len(x), x))
    if n > len(pool):
        raise ValueError(f"{name}: asked for {n} from a pool of {len(pool)}")
    ids = sorted(random.Random(seed).sample(pool, n), key=lambda x: (len(x), x))
    rec = {"name": name, "split": split, "n": n, "seed": seed, "pool_size": len(pool), "drawn_on": date.today().isoformat(),
           "note": note, "sha256": ids_hash(ids), "ids": ids}
    SAMPLES.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rec, indent=1) + "\n", encoding="utf-8")
    return rec


def load(name: str) -> dict:
    path = SAMPLES / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"{path} does not exist; run `python evals/freeze_samples.py` first")
    rec = json.loads(path.read_text(encoding="utf-8"))
    if ids_hash(rec["ids"]) != rec["sha256"]:
        raise ValueError(f"sample {name} does not match its recorded hash; it was edited after it was drawn")
    return rec


def short(rec: dict) -> str:
    return rec["sha256"][:12]
