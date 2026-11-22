from __future__ import annotations

import json
from pathlib import Path

MODULE_ID = "13_validate_llm_weight_influence"


def read_output(root: Path, name="llm_assisted_pws.json"):
    return json.loads((root / "data" / "pipeline" / MODULE_ID / name).read_text(encoding="utf-8"))
