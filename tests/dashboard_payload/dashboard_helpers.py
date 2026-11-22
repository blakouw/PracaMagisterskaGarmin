from __future__ import annotations

import json
from pathlib import Path
from typing import Any

MODULE_ID = "15_build_dashboard_payload"
ASSISTED_ID = "13_validate_llm_weight_influence"


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def artifact(root: Path, module: str, name: str, payload: Any) -> None:
    write_json(root / "data" / "pipeline" / module / name, payload)


def write_assisted(
    root: Path,
    status: str = "completed_assisted_score_computed",
    date: str = "2026-01-03",
    computed: bool = True,
) -> None:
    record = {
        "date": date,
        "pws_deterministic": 75.34 if date == "2026-01-02" else 90.0,
        "pws_llm_assisted": 89.9 if computed else None,
        "pws_llm_assisted_computed": computed,
        "pws_llm_assisted_label_id": "strong" if computed else None,
        "pws_llm_assisted_label": "wysoki" if computed else None,
        "pws_llm_assisted_delta_from_deterministic": -0.1 if computed else None,
        "validated_llm_adjusted_weights": {"LQ": 0.19, "REC": 0.35, "CAP": 0.16, "VS": 0.3} if computed else None,
        "llm_adjustment_applied": computed,
    }
    artifact(
        root,
        ASSISTED_ID,
        "llm_assisted_pws.json",
        {
            "module_id": ASSISTED_ID,
            "status": status,
            "ready_for_next_module": True,
            "record": record,
        },
    )
    artifact(
        root,
        ASSISTED_ID,
        "llm_assisted_pws_quality_report.json",
        {"status": status, "ready_for_next_module": True},
    )
    artifact(
        root,
        ASSISTED_ID,
        "llm_validation_report.json",
        {
            "validation_status": "accepted"
            if computed and status == "completed_assisted_score_computed"
            else "not_applicable"
        },
    )


def read_output(root: Path, name: str = "dashboard_payload.json") -> Any:
    path = root / "data" / "pipeline" / MODULE_ID / name
    return json.loads(path.read_text(encoding="utf-8"))
