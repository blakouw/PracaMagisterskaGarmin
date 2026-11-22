from helpers import read_output
def test_quality(module13, fake_root):
    module13.run(["--dry-run"], root=fake_root)
    assert read_output(fake_root,"llm_assisted_pws_quality_report.json")["optional_module"] is True
