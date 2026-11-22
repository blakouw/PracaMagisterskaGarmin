import json
from helpers import read_output
def test_goal_context_validation(module13, fake_root):
    p=fake_root/"data/local_context/llm_user_goal_context.json"
    p.write_text(json.dumps({"goal_type":"recovery_focus","goal_summary":"short","valid_from":"2026-01-01"}))
    module13.run(["--dry-run"], root=fake_root)
    assert read_output(fake_root,"llm_request_audit.json")["structured_context"]["approved_user_goal_context"]["goal_type"] == "recovery_focus"
