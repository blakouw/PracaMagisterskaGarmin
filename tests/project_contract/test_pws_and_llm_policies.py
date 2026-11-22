import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read_json(relative_path: str) -> dict:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def test_project_settings_contract() -> None:
    settings = read_json("config/project_settings.json")
    assert settings["project_mode"] == "local_single_user"
    assert settings["architecture_mode"] == "modular_artifact_pipeline"
    assert settings["primary_data_source"] == "garmin_workbook"
    assert settings["pipeline_output_root"] == "data/pipeline"
    assert settings["local_secrets_root"] == "data/local_secrets"
    assert settings["previous_project_runtime_dependency_allowed"] is False
    assert settings["previous_project_reference_allowed"] is True
    assert settings["previous_project_one_time_secret_copy_allowed"] is True
    assert settings["default_pws_mode"] == "deterministic"
    assert settings["llm_enabled_by_default"] is False


def test_pws_policy_contract() -> None:
    policy = read_json("config/pws_policy_v1.json")
    assert policy["policy_version"] == "pws_policy_v1"
    assert policy["score_range"] == {"minimum": 0, "maximum": 100}
    assert set(policy["components"]) == {"LQ", "REC", "CAP", "VS"}
    assert sum(policy["base_weights"].values()) == 1.0
    assert policy["weight_constraints"]["minimum_component_weight"] == 0.15
    assert policy["weight_constraints"]["maximum_component_weight"] == 0.40
    assert "LLM must not calculate raw PWS components." in policy["safety_rules"]


def test_llm_policy_contract() -> None:
    policy = read_json("config/llm_policy_v1.json")
    assisted_policy = read_json("config/llm_assisted_pws_policy_v1.json")
    assert policy["policy_version"] == "llm_policy_v1"
    assert policy["supported_modes"] == ["off", "advisory"]
    assert policy["default_mode"] == "off"
    assert "pws_components_today" in policy["allowed_input_scope"]
    assert "bounded_weight_adjustments" in policy["allowed_output_scope"]
    assert "access_auth_tokens" in policy["forbidden_behaviors"]
    constraints = policy["weight_influence_constraints"]
    validation = assisted_policy["validation_policy"]
    assert constraints["maximum_adjustment_per_component"] == validation["maximum_absolute_delta_per_component"]
    assert constraints["maximum_total_weight_shift"] == validation["maximum_total_absolute_delta"]
    assert constraints["requires_deterministic_validation"] is True
    assert policy["fallback_required"] is True
