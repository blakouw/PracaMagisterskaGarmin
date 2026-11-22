from dashboard_helpers import artifact, read_output, write_assisted


def test_weights_copied(module15, fake_root):
    module15.build(fake_root)
    assert read_output(fake_root)["time_series"][1]["weight_lq"] == 0.259268


def test_assisted_weight_histories_are_copied(module15, fake_root):
    write_assisted(fake_root, date="2026-01-01", computed=True)
    artifact(
        fake_root,
        "13_validate_llm_weight_influence",
        "openai_assisted_pws.json",
        {
            "module_id": "13_validate_llm_weight_influence",
            "status": "completed_openai_assisted_scores",
            "ready_for_next_module": True,
            "records": [
                {
                    "date": "2026-01-01",
                    "provider": "openai",
                    "model": "test-model",
                    "pws_llm_assisted": 89.5,
                    "pws_openai_assisted": 89.5,
                    "pws_llm_assisted_computed": True,
                    "pws_openai_assisted_computed": True,
                    "pws_llm_assisted_label_id": "strong",
                    "pws_llm_assisted_delta_from_deterministic": -0.5,
                    "validated_llm_adjusted_weights": {"LQ": 0.18, "REC": 0.32, "CAP": 0.2, "VS": 0.3},
                    "llm_assisted_status": "accepted_adjustment_applied",
                }
            ],
        },
    )

    module15.build(fake_root)
    row = read_output(fake_root)["time_series"][0]
    assert row["local_llm_weight_lq"] == 0.19
    assert row["local_llm_weight_cap"] == 0.16
    assert row["openai_weight_lq"] == 0.18
    assert row["openai_weight_cap"] == 0.2
