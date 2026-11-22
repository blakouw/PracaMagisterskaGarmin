from dashboard_helpers import read_output
def test_schema(module15, fake_root):
    module15.build(fake_root)
    assert read_output(fake_root,"dashboard_payload_schema.json")["primary_score"]["source"] == "pws_deterministic"

