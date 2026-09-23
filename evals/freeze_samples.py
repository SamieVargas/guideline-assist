"""Draw the frozen test samples once, seeded, and write them with their hash.

    python evals/freeze_samples.py           # draws any sample not yet on disk
    python evals/freeze_samples.py --force   # redraws all (shows up in git)

Nothing is drawn from train or dev here; nothing is tuned on these.
"""

import argparse
import sys

from common import ROOT  # noqa: F401  (puts the repo on sys.path)
from core import samples
from core.data import load_split
from core.points import compliant

PLAN = [
    # name, n, seed, pool, note
    ("assist_100", 100, 20260923, "test", "Parts 3 and 4: turn-level assist, both arms, both models"),
    ("intent_300", 300, 20260924, "test", "Part 5: conversation-level intent"),
    ("qa_100", 100, 20260925, "test:compliant", "Part 6: untouched conversations whose gold actions show every required step in guideline order"),
    ("shadow_50", 50, 20260926, "assist_100", "Part 8: a subset of assist_100, so the Part 4 responses serve it without a second bill"),
]


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--force", action="store_true")
    args = p.parse_args(argv)
    test = load_split("test")
    pools = {"test": [c["id"] for c in test], "test:compliant": [c["id"] for c in test if compliant(c)]}
    for name, n, seed, pool, note in PLAN:
        if pool not in pools:
            pools[pool] = samples.load(pool)["ids"]
        try:
            rec = samples.draw(name, pools[pool], n=n, seed=seed, split="test", note=f"{note} (pool: {pool})", force=args.force)
            print(f"drew   {name}: n={rec['n']} from {rec['pool_size']} · seed {seed} · sha256 {rec['sha256'][:12]}")
        except FileExistsError:
            rec = samples.load(name)
            print(f"exists {name}: n={rec['n']} · seed {rec['seed']} · sha256 {rec['sha256'][:12]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
