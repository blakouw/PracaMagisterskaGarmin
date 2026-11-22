from helpers import read_output
def test_module_execution(module13, fake_root):
    assert module13.run(["--dry-run"], root=fake_root) == 0
    assert read_output(fake_root)["ready_for_next_module"] is True
