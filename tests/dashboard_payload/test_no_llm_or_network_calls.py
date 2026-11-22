from dashboard_helpers import read_output
def test_no_llm(module15, fake_root):
    module15.build(fake_root)
    assert read_output(fake_root)["disclosures"]["no_llm_called_in_this_module"] is True

