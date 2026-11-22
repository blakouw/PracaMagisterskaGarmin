import json


ASSISTED_ID = "13_validate_llm_weight_influence"


def artifact(root, module, name, payload):
    path = root / "data" / "pipeline" / module / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def read_output(root, name="dashboard_payload.json"):
    return json.loads((root / "data" / "pipeline" / "15_build_dashboard_payload" / name).read_text(encoding="utf-8"))


def test_multiple_assisted_dates_are_joined_into_time_series(module15, fake_root):
    records = [
        {
            "date": "2026-01-01",
            "pws_deterministic": 90.0,
            "pws_llm_assisted": 89.9,
            "pws_llm_assisted_computed": True,
            "pws_llm_assisted_label_id": "strong",
            "pws_llm_assisted_label": "wysoki",
            "pws_llm_assisted_delta_from_deterministic": -0.1,
            "validated_llm_adjusted_weights": {"LQ": .19, "REC": .35, "CAP": .16, "VS": .3},
            "llm_adjustment_applied": True,
            "llm_called": True,
            "llm_assisted_status": "accepted_adjustment_applied",
        },
        {
            "date": "2026-01-02",
            "pws_deterministic": 75.34,
            "pws_llm_assisted": 74.8,
            "pws_llm_assisted_computed": True,
            "pws_llm_assisted_label_id": "balanced",
            "pws_llm_assisted_label": "stabilny",
            "pws_llm_assisted_delta_from_deterministic": -0.54,
            "validated_llm_adjusted_weights": {"LQ": .249268, "REC": .409986, "CAP": 0.0, "VS": .340746},
            "llm_adjustment_applied": True,
            "llm_called": True,
            "llm_assisted_status": "accepted_adjustment_applied",
        },
    ]
    artifact(fake_root, ASSISTED_ID, "llm_assisted_pws.json", {
        "module_id": ASSISTED_ID,
        "status": "completed_assisted_score_computed",
        "ready_for_next_module": True,
        "records": records,
        "record": records[-1],
    })
    artifact(fake_root, ASSISTED_ID, "llm_assisted_pws_quality_report.json", {
        "status": "completed_assisted_score_computed",
        "ready_for_next_module": True,
    })
    artifact(fake_root, ASSISTED_ID, "llm_validation_report.json", {
        "validation_status": "accepted",
        "records": [
            {"selected_date": "2026-01-01", "validation_status": "accepted"},
            {"selected_date": "2026-01-02", "validation_status": "accepted"},
        ],
    })

    assert module15.build(fake_root)[0] == 0
    payload = read_output(fake_root)
    rows = {row["date"]: row for row in payload["time_series"]}
    assert rows["2026-01-01"]["optional_assisted_pws"] == 89.9
    assert rows["2026-01-02"]["optional_assisted_pws"] == 74.8
    assert rows["2026-01-03"]["optional_assisted_pws"] is None
    assert payload["quality_and_coverage"]["presentation_availability"]["optional_assisted_score_count"] == 2
