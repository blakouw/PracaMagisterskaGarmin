from helpers import read_output
def test_llm_disabled_by_default(module13, fake_root):
    module13.run([], root=fake_root)
    assert read_output(fake_root)["status"] == "skipped_llm_disabled"
