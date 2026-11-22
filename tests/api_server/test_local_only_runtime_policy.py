def test_local_only_runtime_policy(api_app_module):
    errors = api_app_module.validate_api_policy({"policy_version":"dashboard_snapshot_api_policy_v1","runtime":{"default_host":"0.0.0.0","allow_host_override":True,"approved_for_public_exposure":True,"approved_for_lan_exposure":True},"http_policy":{"read_only":True,"allowed_methods":["GET"]},"cors_policy":{"enabled_by_default":False,"allow_wildcard_origins":False}})
    assert any(e["code"] == "PUBLIC_HOST_BINDING_PROHIBITED" for e in errors)
