from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "pipeline/18_angular_dashboard_ui/app/src"


def test_no_llm_or_pipeline_trigger_features():
    text = "\n".join(
        path.read_text(encoding="utf-8").lower()
        for path in SRC.rglob("*")
        if path.is_file() and not path.name.endswith(".test.tsx") and "test" not in path.parts
    )
    for forbidden in [
        "run-pipeline",
        "refresh_from_garmin",
        "sync garmin",
        "apply_llm",
        "api.openai.com",
        "new openai(",
        "openai.responses",
        "authorization: bearer",
    ]:
        assert forbidden not in text
    assert "optional_assisted_pws" in text
    assert "external_assisted_pws" in text
