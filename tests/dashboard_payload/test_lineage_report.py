from dashboard_helpers import read_output
def test_lineage(module15, fake_root):
    module15.build(fake_root)
    lin=read_output(fake_root,"dashboard_payload_lineage.json")
    assert lin["transformation_policy"]["analytical_recomputation_performed"] is False

