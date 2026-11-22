from __future__ import annotations

from registry_helpers import ROOT, contract, modules_by_id, read_json


def module_contract_if_present(module_id: str) -> dict | None:
    path = ROOT / "pipeline" / module_id / "contract.json"
    return contract(module_id) if path.is_file() else None


def test_deterministic_pws_contract_is_primary_and_not_llm_required() -> None:
    c = module_contract_if_present("12_compute_pws_score")
    assert c is not None
    text = (c["responsibility"] + " " + " ".join(c["prohibited_responsibilities"])).lower()
    assert "deterministic" in text
    assert "call_llm" in c["prohibited_responsibilities"]
    assert "calculate_llm_assisted_pws" in c["prohibited_responsibilities"]


def test_optional_llm_assisted_contract_is_optional_and_guardrailed() -> None:
    c = module_contract_if_present("13_validate_llm_weight_influence")
    assert c is not None
    assert c["optional"] is True
    responsibility = c["responsibility"].lower()
    assert "separate" in responsibility
    assert "without modifying deterministic pws" in responsibility
    assert "bypass_guardrails" in c["prohibited_responsibilities"]


def test_dashboard_payload_preserves_primary_boundary_without_recomputation() -> None:
    c = module_contract_if_present("15_build_dashboard_payload")
    assert c is not None
    prohibited = set(c["prohibited_responsibilities"])
    assert "recompute_pws_deterministic" in prohibited
    assert "recompute_pws_llm_assisted" in prohibited
    assert "implement_api_server" in prohibited
    assert "implement_user_interface" in prohibited
    policy = read_json("config/dashboard_payload_policy_v1.json")
    assert policy["primary_score_policy"]["primary_score_type"] == "deterministic"
    assert policy["primary_score_policy"]["assisted_score_must_never_replace_primary"] is True


def test_snapshot_publication_is_copy_only_and_private() -> None:
    c = module_contract_if_present("16_persist_local_snapshot")
    assert c is not None
    policy = read_json("config/dashboard_snapshot_policy_v1.json")
    assert policy["publication_policy"]["history_snapshot_is_immutable"] is True
    assert policy["primary_and_assisted_boundary"]["snapshot_must_not_modify_either_score"] is True
    assert "recompute_pws_deterministic" in c["prohibited_responsibilities"]


def test_local_api_is_local_readonly_and_does_not_trigger_pipeline() -> None:
    c = module_contract_if_present("17_local_api_server")
    assert c is not None
    runtime = c["runtime"]
    assert runtime["host"] == "127.0.0.1"
    assert runtime["local_only"] is True
    assert runtime["read_only"] is True
    assert runtime["public_exposure_approved"] is False
    prohibited = set(c["prohibited_responsibilities"])
    assert "implement_write_endpoints" in prohibited
    assert "implement_authentication" in prohibited
    assert "implement_garmin_token_pipeline" in prohibited
    assert "implement_pipeline_trigger_endpoints" in prohibited


def test_local_ui_consumes_api_without_direct_private_file_reads_or_recompute() -> None:
    c = module_contract_if_present("18_angular_dashboard_ui")
    assert c is not None
    prohibited = set(c["prohibited_responsibilities"])
    assert "read_pipeline_files_directly_from_browser" in prohibited
    assert "read_published_snapshot_files_directly_from_browser" in prohibited
    assert "recompute_pws_deterministic" in prohibited
    assert "trigger_pipeline" in prohibited
    assert "implement_authentication" in prohibited
    policy = read_json("config/local_dashboard_ui_policy_v1.json")
    assert policy["source_api"]["base_path"] == "/api/v1"
    assert policy["presentation_policy"]["primary_score"]["required_score_type"] == "deterministic"


def test_windows_package_is_portable_local_and_private_data_free() -> None:
    c = module_contract_if_present("19_packaging_windows")
    assert c is not None
    runtime = c["runtime"]
    assert runtime["type"] == "portable_windows_localhost_bundle"
    assert runtime["host"] == "127.0.0.1"
    assert runtime["local_only"] is True
    assert runtime["uses_vite_dev_server"] is False
    assert runtime["packages_private_data"] is False
    prohibited = set(c["prohibited_responsibilities"])
    assert "create_installer" in prohibited
    assert "public_deployment" in prohibited
    assert "run_full_pipeline" in prohibited
    assert "sync_garmin_data" in prohibited
    assert "package_private_snapshots" in prohibited
    assert "package_tokens_or_secrets" in prohibited


def test_planned_launcher_boundary_is_not_required_when_launcher_is_not_registered() -> None:
    registered = modules_by_id()
    launcher_ids = {module_id for module_id in registered if "launcher" in module_id or "local_app_runtime" in module_id}
    for module_id in launcher_ids:
        c = contract(module_id)
        prohibited = set(c.get("prohibited_responsibilities", []))
        assert "run_full_pipeline" in prohibited or "trigger_pipeline" in prohibited
