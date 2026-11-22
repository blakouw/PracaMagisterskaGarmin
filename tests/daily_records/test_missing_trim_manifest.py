from daily_helpers import copy_policy, output_dir, read_json

def test_missing_trim_manifest_blocks(module05, case_root) -> None:
    copy_policy(case_root)
    assert module05.execute(root=case_root) != 0
    run = read_json(output_dir(case_root) / "run_manifest.json")
    assert run["domain_status"] == "blocked_missing_trim_manifest"
    errors = read_json(output_dir(case_root) / "errors.json")
    assert any(e["code"] == "TRIMMED_SHEETS_MANIFEST_NOT_FOUND" for e in errors["errors"])
