from __future__ import annotations

from registry_helpers import modules_by_id, registry_modules


def test_all_dependencies_reference_existing_modules_and_not_self() -> None:
    ids = set(modules_by_id())
    for module in registry_modules():
        for dependency in module.get("depends_on", []):
            assert dependency in ids, f"{module['id']} depends on missing {dependency}"
            assert dependency != module["id"], module["id"]


def test_dependency_graph_has_no_cycles() -> None:
    modules = modules_by_id()
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(module_id: str, stack: list[str]) -> None:
        assert module_id not in visiting, "cycle: " + " -> ".join(stack + [module_id])
        if module_id in visited:
            return
        visiting.add(module_id)
        for dependency in modules[module_id].get("depends_on", []):
            visit(dependency, stack + [module_id])
        visiting.remove(module_id)
        visited.add(module_id)

    for module_id in modules:
        visit(module_id, [])


def test_dependencies_do_not_point_forward_in_registry_order() -> None:
    order = {module["id"]: module["order"] for module in registry_modules()}
    for module in registry_modules():
        for dependency in module.get("depends_on", []):
            assert order[dependency] < module["order"], f"{module['id']} depends on non-earlier {dependency}"


def test_application_layer_chronology_when_modules_exist() -> None:
    modules = modules_by_id()
    if "15_build_dashboard_payload" in modules:
        assert {"08_compute_load_metrics", "09_compute_readiness", "10_compute_pws_components", "11_compute_pws_weights", "12_compute_pws_score"} <= set(modules["15_build_dashboard_payload"]["depends_on"])
    if "16_persist_local_snapshot" in modules:
        assert "15_build_dashboard_payload" in modules["16_persist_local_snapshot"]["depends_on"]
    if "17_local_api_server" in modules:
        assert "16_persist_local_snapshot" in modules["17_local_api_server"]["depends_on"]
    if "18_angular_dashboard_ui" in modules:
        assert "17_local_api_server" in modules["18_angular_dashboard_ui"]["depends_on"]
    if "19_packaging_windows" in modules:
        assert {"17_local_api_server", "18_angular_dashboard_ui"} <= set(modules["19_packaging_windows"]["depends_on"])


def test_project_contract_has_no_dependencies() -> None:
    assert modules_by_id()["00_project_contract"]["depends_on"] == []
