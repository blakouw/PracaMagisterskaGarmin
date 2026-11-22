from dashboard_helpers import read_output
def test_json(module15, fake_root):
    module15.build(fake_root)
    assert read_output(fake_root)["payload_type"] == "local_dashboard_presentation_payload"

