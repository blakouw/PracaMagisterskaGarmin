from activity_ingest_helpers import public_config


def test_public_config_is_safe_and_disabled_by_default() -> None:
    config = public_config()
    assert config["policy_version"] == "garmin_activity_ingest_v1"
    assert config["enabled"] is False
    assert config["optional_module"] is True
    assert config["client_library"] == "garminconnect"
    assert config["credentials_mode"] == "local_tokenstore_only"
    assert config["previous_project_runtime_dependency_allowed"] is False
    assert config["local_tokenstore_directory"] == "data/local_secrets/garmin_tokenstore"
    assert config["manual_activity_ids"] == []
    assert config["privacy_rules"]["never_log_token_values"] is True
