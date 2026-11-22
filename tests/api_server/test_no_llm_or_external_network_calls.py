import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def test_no_external_sdk_clients_imported_and_chat_llm_is_local_only():
    tree = ast.parse((ROOT / "pipeline/17_local_api_server/api_app.py").read_text(encoding="utf-8"))
    imports = {alias.name for node in tree.body if isinstance(node, ast.Import) for alias in node.names}
    assert "requests" not in imports
    assert "openai" not in imports
    policy = json.loads((ROOT / "config/llm_policy_v1.json").read_text(encoding="utf-8"))
    assert policy["endpoint"].startswith("http://127.0.0.1:")
