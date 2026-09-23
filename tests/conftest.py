import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "evals"))
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "scripts"))


@pytest.fixture(autouse=True)
def isolated_cache(tmp_path, monkeypatch):
    """No test reads or writes the real response cache."""
    import core.llm
    monkeypatch.setattr(core.llm, "CACHE_DIR", tmp_path / "llm-cache")
