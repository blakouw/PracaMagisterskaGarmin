from dashboard_helpers import read_output
def test_quality_report(module15, fake_root):
    module15.build(fake_root)
    assert read_output(fake_root,"dashboard_payload_quality_report.json")["ready_for_next_module"] is True

