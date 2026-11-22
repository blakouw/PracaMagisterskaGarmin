from dashboard_helpers import read_output
def test_components_copied(module15, fake_root):
    module15.build(fake_root)
    assert read_output(fake_root)["current_state"]["pws_components"]["LQ"]["score"] == 81.0

