from __future__ import annotations

from registry_helpers import ROOT, contract, registry_modules


REQUIRED_CONTRACT_FIELDS = {
    "module_id",
    "module_name",
    "version",
    "status",
    "optional",
    "responsibility",
    "depends_on",
    "inputs",
    "outputs",
    "run_command",
    "artifact_directory",
    "test_directory",
    "visualization_directory",
    "prohibited_responsibilities",
    "data_sensitivity",
    "notes",
}


def test_implemented_module_contracts_have_required_shape() -> None:
    for module in registry_modules():
        if module["status"] != "implemented":
            continue
        module_id = module["id"]
        module_contract = contract(module_id)
        assert REQUIRED_CONTRACT_FIELDS <= set(module_contract), module_id
        assert module_contract["module_id"] == module_id
        assert module_contract["status"] == module["status"]
        assert module_contract["optional"] == module["optional"]
        assert module_contract["responsibility"].strip()
        assert isinstance(module_contract["depends_on"], list)
        assert isinstance(module_contract["inputs"], list)
        assert isinstance(module_contract["outputs"], list)
        assert isinstance(module_contract["prohibited_responsibilities"], list)


def test_implemented_modules_have_readme_contract_and_run_script() -> None:
    for module in registry_modules():
        if module["status"] != "implemented":
            continue
        module_id = module["id"]
        module_dir = ROOT / "pipeline" / module_id
        module_contract = contract(module_id)
        assert (module_dir / "README.md").is_file(), module_id
        assert (module_dir / "contract.json").is_file(), module_id
        run_command = module_contract.get("run_command")
        assert run_command, module_id
        assert (ROOT / run_command).is_file(), run_command


def test_declared_test_and_visualization_directories_exist_for_implemented_modules() -> None:
    for module in registry_modules():
        if module["status"] != "implemented":
            continue
        module_contract = contract(module["id"])
        test_dir = module_contract.get("test_directory")
        visualization_dir = module_contract.get("visualization_directory")
        if test_dir:
            assert (ROOT / test_dir).is_dir(), test_dir
        if visualization_dir:
            assert (ROOT / visualization_dir).is_dir(), visualization_dir


def test_build_and_validation_commands_exist_when_declared() -> None:
    for module in registry_modules():
        module_contract = contract(module["id"])
        for field in ["build_command", "validation_command"]:
            command = module_contract.get(field)
            if command:
                assert (ROOT / command).is_file(), f"{module['id']} {field}: {command}"


def test_contracts_do_not_approve_public_exposure_or_previous_project_runtime() -> None:
    for module in registry_modules():
        module_contract = contract(module["id"])
        runtime = module_contract.get("runtime", {})
        if isinstance(runtime, dict):
            assert runtime.get("public_exposure_approved") is not True, module["id"]
            assert runtime.get("public_deployment_approved") is not True, module["id"]
            assert runtime.get("lan_exposure_approved") is not True, module["id"]
        prohibited = set(module_contract.get("prohibited_responsibilities", []))
        if module["id"] != "00_project_contract":
            assert "depend_on_previous_project_runtime" in prohibited or module["id"].startswith("14_")
