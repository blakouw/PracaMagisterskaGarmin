from dashboard_helpers import read_output
def test_latest_null(module15, fake_root):
    module15.build(fake_root)
    current=read_output(fake_root)["current_state"]
    assert current["date"]=="2026-01-03"
    assert current["primary_pws"]["score"] is None

