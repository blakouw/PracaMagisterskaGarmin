from snapshotapi_fixtures import load_ctx

def test_chat_endpoint_uses_injected_local_llm_without_modifying_snapshot(tmp_path, api_app_module):
    ctx = load_ctx(tmp_path, api_app_module)
    def fake_llm(messages, context, policy):
        assert context["latest_data_date"] == "2026-01-03"
        assert policy["endpoint"].startswith("http://127.0.0.1:")
        assert messages[-1]["content"] == "Explain PWS"
        return "Synthetic local LLM answer."
    code, payload = api_app_module.handle_post(ctx, "/api/v1/dashboard/chat", {"message": "Explain PWS"}, llm_client=fake_llm)
    assert code == 200
    assert payload["answer"] == "Synthetic local LLM answer."
    assert payload["llm_called"] is True
    assert payload["persisted"] is False
    assert payload["snapshot_modified"] is False
    assert payload["pipeline_triggered"] is False

def test_chat_endpoint_rejects_empty_message(tmp_path, api_app_module):
    ctx = load_ctx(tmp_path, api_app_module)
    code, payload = api_app_module.handle_post(ctx, "/api/v1/dashboard/chat", {"message": ""}, llm_client=lambda **_: "unused")
    assert code == 400
    assert payload["code"] == "CHAT_MESSAGE_INVALID"
