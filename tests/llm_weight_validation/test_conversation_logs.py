import json

from helpers import FakeLLM


def test_per_date_conversation_log_preserves_interpretation_evidence(module13, fake_root, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    fake = FakeLLM(module13, {
        "decision": "propose_adjustment",
        "reason_summary": "Synthetic large shift for audit.",
        "proposed_weight_deltas": {"LQ": -0.15, "REC": 0.15, "CAP": 0.0, "VS": 0.0},
    })

    result = module13.run(
        ["--enable-llm", "--date", "2026-01-01"],
        injected_llm_client=fake,
        root=fake_root,
    )

    assert result == 0
    path = fake_root / "data" / "pipeline" / "13_validate_llm_weight_influence" / "llm_conversations" / "2026-01-01.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["system_instruction"]
    assert payload["structured_context"]["date"] == "2026-01-01"
    assert payload["parsed_model_response"]["reason_summary"] == "Synthetic large shift for audit."
    assert payload["raw_proposal_validation_status"] == "rejected_guardrail_violation"
    assert payload["final_interpretation_status"] == "accepted_with_normalization_warnings"
    assert payload["guardrail_findings"]
    assert payload["effective_assisted_weights"]
    assert payload["hidden_reasoning_stored"] is False
