from helpers import read_output, FakeLLM


def test_guardrail_finding_is_normalized_and_score_is_preserved(module13, fake_root, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY","x")
    fake=FakeLLM(module13, {"decision":"propose_adjustment","reason_summary":"x","proposed_weight_deltas":{"LQ":-0.15,"REC":0.15,"CAP":0,"VS":0}})
    module13.run(["--enable-llm","--date","2026-01-01"], injected_llm_client=fake, root=fake_root)
    record = read_output(fake_root)["record"]
    assert record["pws_llm_assisted"] is not None
    assert record["llm_raw_proposal_validation_status"] == "rejected_guardrail_violation"
    assert record["llm_proposal_validation_status"] == "accepted_with_normalization_warnings"
    assert record["proposal_interpretation_mode"] == "permissive_simplex_normalization"
    assert record["llm_guardrail_violations"]
