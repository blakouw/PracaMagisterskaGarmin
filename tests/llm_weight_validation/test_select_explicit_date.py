from helpers import read_output
def test_select_explicit_date(module13, fake_root):
    module13.run(["--dry-run","--date","2026-01-01"], root=fake_root)
    assert read_output(fake_root)["execution_scope"]["selected_date"] == "2026-01-01"
