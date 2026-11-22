from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_local_secrets_directory_is_documented_and_ignored() -> None:
    readme = ROOT / "data" / "local_secrets" / "README.md"
    assert readme.is_file()
    text = readme.read_text(encoding="utf-8")
    assert "Do not commit real secrets" in text
    assert "must never depend on the old project at runtime" in text

    gitignore_lines = {
        line.strip().replace("\\", "/")
        for line in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    }
    assert (
        "data/local_secrets/" in gitignore_lines
        or "data/local_secrets" in gitignore_lines
        or "data/local_secrets/*" in gitignore_lines
    )


def test_private_garmin_and_secret_patterns_are_ignored() -> None:
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for pattern in [
        "garmin_export_*.xlsx",
        "data/garmin_tokens/",
        "**/tokenstore*",
        "**/*oauth*.json",
        ".env",
        "data/pipeline/**/*.parquet",
        "data/pipeline/**/*.csv",
        "*.log",
    ]:
        assert pattern in gitignore


def test_public_config_files_are_not_ignored_by_rule() -> None:
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for pattern in [
        "!config/project_settings.json",
        "!config/pipeline_modules.json",
        "!config/pws_policy_v1.json",
        "!config/llm_policy_v1.json",
    ]:
        assert pattern in gitignore
