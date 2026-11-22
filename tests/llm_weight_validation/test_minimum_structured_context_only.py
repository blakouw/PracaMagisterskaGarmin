from helpers import read_output
def test_minimum_context(module13, fake_root):
    module13.run(["--dry-run"], root=fake_root)
    ctx=read_output(fake_root,"llm_request_audit.json")["structured_context"]
    assert set(ctx) <= {"date","available_components","missing_components","component_scores","component_statuses","component_coverage_information","pws_deterministic","deterministic_effective_weights","overlap_disclosures","guardrail_limits","approved_user_goal_context"}
