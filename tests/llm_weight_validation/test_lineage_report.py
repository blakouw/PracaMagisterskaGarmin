from helpers import read_output
def test_lineage(module13, fake_root):
    module13.run(["--dry-run"], root=fake_root)
    boundary = read_output(fake_root,"llm_assisted_pws_lineage.json")["llm_boundary"]
    assert boundary["maximum_calls_per_eligible_date"] == 1
    assert boundary["maximum_calls_per_run"] == 2
    assert boundary["selected_dates"] == ["2026-01-01", "2026-01-02"]
