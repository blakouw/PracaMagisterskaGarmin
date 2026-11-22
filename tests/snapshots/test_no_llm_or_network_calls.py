import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def test_no_llm_or_network_imports():
    tree = ast.parse((ROOT / "pipeline/16_persist_local_snapshot/main.py").read_text(encoding="utf-8-sig"))
    imports = {alias.name for node in tree.body if isinstance(node, ast.Import) for alias in node.names}
    assert "requests" not in imports
    assert "openai" not in imports
