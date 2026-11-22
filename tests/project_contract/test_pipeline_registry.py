from __future__ import annotations

from collections import Counter

from registry_helpers import REMOVED_MODULE_IDS, ROOT, contract, registry, registry_modules


REQUIRED_REGISTRY_FIELDS = {
    "id",
    "order",
    "name",
    "status",
    "optional",
    "responsibility",
    "depends_on",
    "expected_inputs",
    "expected_outputs",
    "prohibited_responsibilities",
}
ALLOWED_STATUSES = {"planned", "implemented"}


def test_pipeline_registry_json_shape() -> None:
    payload = registry()
    assert payload["registry_version"]
    assert isinstance(payload["modules"], list)
    assert payload["modules"]


def test_pipeline_registry_ids_are_unique_and_ordered() -> None:
    modules = registry_modules()
    ids = [module["id"] for module in modules]
    assert [item for item, count in Counter(ids).items() if count > 1] == []
    assert [module["order"] for module in modules] == list(range(len(modules)))


def test_registry_entries_have_required_fields_and_allowed_statuses() -> None:
    for module in registry_modules():
        assert REQUIRED_REGISTRY_FIELDS <= set(module), module["id"]
        assert module["status"] in ALLOWED_STATUSES, module["id"]
        assert isinstance(module["depends_on"], list), module["id"]
        assert isinstance(module["expected_inputs"], list), module["id"]
        assert isinstance(module["expected_outputs"], list), module["id"]
        assert module["responsibility"].strip(), module["id"]


def test_implemented_registry_entries_match_pipeline_contracts() -> None:
    for module in registry_modules():
        if module["status"] != "implemented":
            continue
        module_id = module["id"]
        assert (ROOT / "pipeline" / module_id).is_dir(), module_id
        assert (ROOT / "pipeline" / module_id / "contract.json").is_file(), module_id
        module_contract = contract(module_id)
        assert module_contract["module_id"] == module_id
        assert module_contract["status"] == module["status"]


def test_removed_modules_are_not_registered_even_under_obvious_variants() -> None:
    ids = {module["id"] for module in registry_modules()}
    assert ids.isdisjoint(REMOVED_MODULE_IDS)
    for module_id in ids:
        normalized = module_id.lower()
        assert "auth_and_profile" not in normalized
        assert "garmin_token_pipeline" not in normalized
        assert not ("token" in normalized and "garmin" in normalized and "pipeline" in normalized)


def test_registry_has_no_duplicate_responsibility_for_same_module_folder() -> None:
    folders = [module["id"] for module in registry_modules()]
    assert len(folders) == len(set(folders))
