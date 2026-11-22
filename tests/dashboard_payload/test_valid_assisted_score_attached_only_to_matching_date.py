from dashboard_helpers import read_output, write_assisted
def test_assisted_matching(module15, fake_root):
    write_assisted(fake_root, date="2026-01-03")
    module15.build(fake_root)
    rows=read_output(fake_root)["time_series"]
    assert [r["optional_assisted_pws"] for r in rows] == [None, None, 89.9]

