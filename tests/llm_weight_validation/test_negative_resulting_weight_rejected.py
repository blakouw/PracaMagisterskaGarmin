from helpers import FakeLLM, read_output


def test_negative_target_weight_is_reported_and_normalized(module13, fake_root, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY","x")
    fake=FakeLLM(module13, {"decision":"propose_adjustment","reason_summary":"x","proposed_weight_deltas":{"LQ":0.05,"REC":0,"CAP":-0.20,"VS":0.15}})
    module13.run(["--enable-llm","--date","2026-01-01"], injected_llm_client=fake, root=fake_root)
    report = read_output(fake_root,"llm_validation_report.json")
    assert report["raw_validation_status"] == "rejected_guardrail_violation"
    assert report["validation_status"] == "accepted_with_normalization_warnings"
    assert "Resulting weights must not be negative." in report["violations"]
    assert all(value >= 0 for value in report["validated_llm_adjusted_weights"].values())
    assert abs(sum(report["validated_llm_adjusted_weights"].values()) - 1.0) < 1e-9
