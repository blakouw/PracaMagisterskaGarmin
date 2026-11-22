from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
def test_no_previous_project_import():
    text=(ROOT/"pipeline/13_validate_llm_weight_influence/main.py").read_text(encoding="utf-8")
    assert "RepoMagi" not in text
    assert "previous_project" not in text
