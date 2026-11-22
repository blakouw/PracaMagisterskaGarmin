from dashboard_helpers import read_output, write_assisted
def test_rejected(module15, fake_root):
    write_assisted(fake_root, status="completed_proposal_rejected", computed=False)
    module15.build(fake_root)
    assert read_output(fake_root)["current_state"]["optional_assisted_pws"]["status"]=="not_available_proposal_rejected"

