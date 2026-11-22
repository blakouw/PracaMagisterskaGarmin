from __future__ import annotations

import json


ASSISTED_ID = "13_validate_llm_weight_influence"


def artifact(root, module, name, payload):
    path = root / "data" / "pipeline" / module / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def read_output(root, name="dashboard_payload.json"):
    return json.loads((root / "data" / "pipeline" / "15_build_dashboard_payload" / name).read_text(encoding="utf-8"))


def run_module(module15, root):
    return module15.build(root)[0]


def write_external(root):
    records = [
        {
            "date": "2026-01-01",
            "provider": "openai",
            "model": "test-external-model",
            "pws_deterministic": 90.0,
            "pws_llm_assisted": 91.1,
            "pws_llm_assisted_computed": True,
            "pws_openai_assisted": 91.1,
            "pws_openai_assisted_computed": True,
            "pws_llm_assisted_label_id": "strong",
            "pws_llm_assisted_label": "wysoki",
            "pws_llm_assisted_delta_from_deterministic": 1.1,
            "validated_llm_adjusted_weights": {"LQ": 0.19, "REC": 0.34, "CAP": 0.16, "VS": 0.31},
            "llm_adjustment_applied": True,
        },
        {
            "date": "2026-01-02",
            "provider": "openai",
            "model": "test-external-model",
            "pws_deterministic": 75.34,
            "pws_llm_assisted": 76.2,
            "pws_llm_assisted_computed": True,
            "pws_openai_assisted": 76.2,
            "pws_openai_assisted_computed": True,
            "pws_llm_assisted_label_id": "balanced",
            "pws_llm_assisted_label": "stabilny",
            "pws_llm_assisted_delta_from_deterministic": 0.86,
            "validated_llm_adjusted_weights": {"LQ": 0.25, "REC": 0.41, "CAP": 0.0, "VS": 0.34},
            "llm_adjustment_applied": True,
        },
    ]
    artifact(root, ASSISTED_ID, "openai_assisted_pws.json", {
        "module_id": ASSISTED_ID,
        "variant_id": "openai_external",
        "provider": "openai",
        "model": "test-external-model",
        "status": "completed_openai_assisted_scores",
        "records": records,
        "record": records[-1],
        "ready_for_next_module": True,
        "must_not_replace_primary_score": True,
        "must_not_replace_local_llm_variant": True,
    })
    artifact(root, ASSISTED_ID, "openai_assisted_pws_quality_report.json", {
        "status": "completed_openai_assisted_scores",
        "ready_for_next_module": True,
    })


def test_external_variant_is_separate_and_deterministic_remains_primary(module15, fake_root):
    write_external(fake_root)
    code = run_module(module15, fake_root)
    assert code == 0

    payload = read_output(fake_root)
    assert payload["metadata"]["primary_score_type"] == "deterministic"
    assert payload["current_state"]["primary_pws"]["score_type"] == "deterministic"
    assert payload["current_state"]["external_assisted_pws"]["available"] is False
    assert [row["external_assisted_pws"] for row in payload["time_series"]] == [91.1, 76.2, None]
    assert payload["time_series"][0]["pws_deterministic"] == 90.0
    assert payload["quality_and_coverage"]["presentation_availability"]["external_assisted_score_count"] == 2
    assert payload["metadata"]["source_modules"]["pws_openai_assisted"]["artifact_present"] is True


def test_missing_external_artifact_preserves_null_series(module15, fake_root):
    code = run_module(module15, fake_root)
    assert code == 0
    payload = read_output(fake_root)
    assert all(row["external_assisted_pws"] is None for row in payload["time_series"])
    assert payload["current_state"]["external_assisted_pws"]["available"] is False
