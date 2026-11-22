from dashboard_helpers import read_output
def test_disclosures(module15, fake_root):
    module15.build(fake_root)
    d=read_output(fake_root)["disclosures"]
    assert d["no_llm_called_in_this_module"] is True
    assert "not medical" in d["medical_limitation"]

