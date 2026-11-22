from helpers import read_output
def test_all_eligible_dates_processed_per_run(module13, fake_root):
    module13.run(["--dry-run"], root=fake_root)
    scope = read_output(fake_root)["execution_scope"]
    assert scope["maximum_llm_calls_per_eligible_date"] == 1
    assert scope["maximum_llm_calls_per_run"] == 2
    assert scope["selected_dates"] == ["2026-01-01", "2026-01-02"]
    assert scope["processed_records_count"] == 2


def test_one_llm_call_is_made_for_each_eligible_date(module13, fake_root, valid_adjustment, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    module13.run(["--enable-llm"], injected_llm_client=valid_adjustment, root=fake_root)
    output = read_output(fake_root)
    assert valid_adjustment.calls == 2
    assert [record["date"] for record in output["records"]] == ["2026-01-01", "2026-01-02"]
    assert output["record"] == output["records"][-1]
