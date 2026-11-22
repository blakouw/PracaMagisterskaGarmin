import json
from dashboard_helpers import read_output
def test_partial(module15, fake_root):
    p=fake_root/"data/pipeline/12_compute_pws_score/pws_score.json"
    data=json.loads(p.read_text()); data["records"]=data["records"][:2]; p.write_text(json.dumps(data))
    module15.build(fake_root)
    assert any("incomplete component" in d for d in read_output(fake_root)["current_state"]["disclosures"])

