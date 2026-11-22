from dashboard_helpers import read_output, write_assisted
def test_primary(module15, fake_root):
    write_assisted(fake_root, date="2026-01-03")
    module15.build(fake_root)
    assert read_output(fake_root)["current_state"]["primary_pws"]["score_field"] == "pws_deterministic"

