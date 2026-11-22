from dashboard_helpers import read_output, write_assisted
def test_assisted_not_primary(module15, fake_root):
    write_assisted(fake_root, date="2026-01-03")
    module15.build(fake_root)
    out=read_output(fake_root)["current_state"]
    assert out["primary_pws"]["score"] is None
    assert out["optional_assisted_pws"]["must_not_replace_primary_score"] is True

