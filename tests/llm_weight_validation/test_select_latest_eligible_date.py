from helpers import read_output
def test_default_selects_all_eligible_dates_and_keeps_latest_alias(module13, fake_root):
    module13.run(["--dry-run"], root=fake_root)
    output = read_output(fake_root)
    assert output["execution_scope"]["selection_mode"] == "all_eligible_dates"
    assert output["execution_scope"]["selected_dates"] == ["2026-01-01", "2026-01-02"]
    assert output["execution_scope"]["selected_date"] == "2026-01-02"
    assert output["record"] == output["records"][-1]
