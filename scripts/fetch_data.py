"""Download the ABCD files this repo reads, from one pinned commit of
github.com/asappresearch/abcd, and check each against the sha256 recorded
here. The small files (ontology, kb, guidelines, the three-conversation
sample, the licence) are committed under data/abcd/; the 37 MB conversation
file is not, so this is the one step a fresh clone needs before any eval.

    python scripts/fetch_data.py            # fetch what is missing, verify all
    python scripts/fetch_data.py --verify   # verify only, no network
"""

import argparse
import hashlib
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "abcd"

COMMIT = "6b8700ce67c6b37b062dd7a60abc76d7ef832a97"  # asappresearch/abcd main, 2022-01-26
BASE = f"https://raw.githubusercontent.com/asappresearch/abcd/{COMMIT}"

# path in the source repo -> (local name, sha256), hashed on download 2026-09-23.
FILES = {
    "data/abcd_v1.1.json.gz": ("abcd_v1.1.json.gz", "2bdf53ac359543dcdc38d55bc6513e78df120363f8f44870716e909f4606de15"),
    "data/ontology.json": ("ontology.json", "2e1c1d763518ba084ada7f7bc8b54f0b489c81da3b170875cf9340891e06524c"),
    "data/kb.json": ("kb.json", "7b1cdb1002e3353451f9a3c3f389f1eabd8ae5d46c1d76f567c71819711f3857"),
    "data/guidelines.json": ("guidelines.json", "9264557941df24fe075138a632a2345172971573124a354ccb2ceee2a12e4c2a"),
    "data/abcd_sample.json": ("abcd_sample.json", "151e0c487493ab376bb5115538f3bfd6d2f460c94f9daa5cdf04e55bccdf4808"),
    "LICENSE": ("LICENSE", "3ab7e179a7f13027b7bc64293541f0e9beacca3701cade67fb8fce78c2d9317b"),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--verify", action="store_true", help="check hashes only, download nothing")
    args = p.parse_args(argv)
    DATA.mkdir(parents=True, exist_ok=True)
    bad = 0
    for src, (name, want) in FILES.items():
        dest = DATA / name
        if not dest.exists() and not args.verify:
            print(f"fetching {src} ...", flush=True)
            urllib.request.urlretrieve(f"{BASE}/{src}", dest)
        if not dest.exists():
            print(f"MISSING  {name}")
            bad += 1
            continue
        got = sha256(dest)
        ok = got == want
        bad += not ok
        print(f"{'ok      ' if ok else 'MISMATCH'} {name} {got[:16]}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
