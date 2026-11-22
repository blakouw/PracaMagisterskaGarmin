from __future__ import annotations

from synthetic_input_factory import read_project_json


def test_project_settings_define_current_workbook_discovery_policy() -> None:
    settings = read_project_json("config/project_settings.json")
    workbook_config = settings["input_workbook"]

    assert workbook_config["filename_pattern"] == "garmin_export_*.xlsx"
    assert workbook_config["search_directories"] == [".", "data/input"]
    assert workbook_config["recursive"] is False
    assert workbook_config["selection_strategy"] == "first_path_sorted_ascending"
    assert workbook_config["require_exactly_one_match"] is False


def test_current_input_locations_are_declared_in_readme_and_contract() -> None:
    readme = read_project_json("config/project_settings.json")["input_workbook"]
    contract = read_project_json("pipeline/01_find_input_workbook/contract.json")

    assert "." in readme["search_directories"]
    assert "data/input" in readme["search_directories"]
    assert "local filesystem paths explicitly configured as workbook search directories" in contract["inputs"]
    assert "config/project_settings.json" in contract["inputs"]
