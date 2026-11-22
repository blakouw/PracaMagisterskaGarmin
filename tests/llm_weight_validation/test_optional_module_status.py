def test_optional_skip_ready(module13, fake_root):
    assert module13.run(["--dry-run"], root=fake_root) == 0
