from __future__ import annotations

from synthetic_input_factory import MODULE_DIR, MODULE_ID, ROOT, read_project_json


def test_production_module_01_contract_files_exist() -> None:
    assert MODULE_DIR.is_dir()
    assert (MODULE_DIR / "README.md").is_file()
    assert (MODULE_DIR / "contract.json").is_file()
    assert (MODULE_DIR / "main.py").is_file()
    assert (MODULE_DIR / "run.bat").is_file()


def test_contract_matches_pipeline_registry() -> None:
    registry_modules = read_project_json("config/pipeline_modules.json")["modules"]
    registry_entry = next(module for module in registry_modules if module["id"] == MODULE_ID)
    contract = read_project_json(f"pipeline/{MODULE_ID}/contract.json")

    assert contract["module_id"] == MODULE_ID
    assert contract["status"] == registry_entry["status"] == "implemented"
    assert contract["responsibility"] == registry_entry["responsibility"]
    assert contract["depends_on"] == registry_entry["depends_on"] == ["00_project_contract"]
    assert contract["inputs"] == registry_entry["expected_inputs"]
    assert contract["outputs"] == registry_entry["expected_outputs"]
    assert contract["test_directory"] == f"tests/{MODULE_ID}"
    assert contract["visualization_directory"] == f"visualization/{MODULE_ID}"
    assert contract["run_command"] == f"pipeline/{MODULE_ID}/run.bat"
    assert (ROOT / contract["run_command"]).is_file()


def test_contract_responsibility_is_workbook_discovery_only() -> None:
    contract = read_project_json(f"pipeline/{MODULE_ID}/contract.json")
    responsibility = contract["responsibility"].lower()

    assert "workbook" in responsibility
    assert "find" in responsibility or "select" in responsibility
    assert "deterministically" in responsibility

    prohibited = set(contract["prohibited_responsibilities"])
    expected_prohibited = {
        "read_workbook_contents",
        "inspect_xlsx_sheets",
        "inspect_xlsx_columns",
        "trim_workbook",
        "fetch_garmin_api_data",
        "normalize_daily_records",
        "calculate_metrics",
        "calculate_pws",
        "call_llm",
        "implement_api_server",
        "implement_ui",
        "depend_on_previous_project_runtime",
    }
    assert expected_prohibited <= prohibited


def test_contract_does_not_assign_later_stage_responsibilities() -> None:
    contract = read_project_json(f"pipeline/{MODULE_ID}/contract.json")
    text = " ".join(
        [
            contract["responsibility"],
            " ".join(contract.get("inputs", [])),
            " ".join(contract.get("outputs", [])),
        ]
    ).lower()

    forbidden_active_phrases = [
        "parse xlsx",
        "read sheets",
        "read cells",
        "trim columns",
        "normalize records",
        "calculate readiness",
        "calculate pws",
        "dashboard api",
        "user interface",
        "garmin token pipeline",
    ]
    assert [phrase for phrase in forbidden_active_phrases if phrase in text] == []
