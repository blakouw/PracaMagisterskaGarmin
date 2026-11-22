def test_no_network_without_enable(module13, fake_root):
    assert module13.run(["--dry-run"], root=fake_root) == 0
