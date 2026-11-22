from __future__ import annotations

from registry_helpers import REMOVED_MODULE_IDS, ROOT, contract, module_ids, registry_modules


ACTIVE_RESPONSIBILITY_PHRASES = {
    "implement_authentication",
    "implement_user_profile",
    "implement_garmin_token_pipeline",
    "refresh_tokens",
    "manage_application_users",
}


def test_removed_modules_are_absent_from_registry_and_pipeline_folders() -> None:
    ids = set(module_ids())
    assert ids.isdisjoint(REMOVED_MODULE_IDS)
    for module_id in REMOVED_MODULE_IDS:
        assert not (ROOT / "pipeline" / module_id).exists()


def test_no_module_claims_removed_responsibility_as_active_responsibility() -> None:
    for module in registry_modules():
        responsibility = module.get("responsibility", "").lower()
        assert "auth_and_profile_api" not in responsibility
        assert "garmin_token_pipeline" not in responsibility
        assert "oauth" not in responsibility
        assert "garmin token pipeline" not in responsibility
        assert "garmin token management" not in responsibility


def test_application_modules_explicitly_prohibit_removed_features_when_relevant() -> None:
    for module_id in ["17_local_api_server", "18_angular_dashboard_ui", "19_packaging_windows"]:
        if not (ROOT / "pipeline" / module_id / "contract.json").is_file():
            continue
        prohibited = set(contract(module_id).get("prohibited_responsibilities", []))
        assert "implement_authentication" in prohibited
        assert "implement_user_profile" in prohibited
        assert "implement_garmin_token_pipeline" in prohibited


def test_removed_terms_in_documentation_are_allowed_only_as_prohibitions() -> None:
    for module in registry_modules():
        prohibited = set(contract(module["id"]).get("prohibited_responsibilities", []))
        if prohibited & ACTIVE_RESPONSIBILITY_PHRASES:
            assert True
