from activity_ingest_helpers import artifact_dir, run_module, write_config, write_tokenstore


def test_secrets_are_not_logged_or_persisted(module04, case_root) -> None:
    secret_values = ["SECRET_OAUTH1", "SECRET_OAUTH1_SECRET", "SECRET_ACCESS", "SECRET_REFRESH"]
    write_config(case_root, enabled=True, manual_activity_ids=["100"])
    write_tokenstore(case_root, valid=True, secret_prefix="SECRET")
    assert run_module(module04, case_root, dependency=True) == 0
    output_text = ""
    for path in artifact_dir(case_root).rglob("*"):
        if path.is_file() and path.suffix.lower() not in {".fit", ".tcx"}:
            output_text += path.read_text(encoding="utf-8", errors="ignore")
    for value in secret_values:
        assert value not in output_text
