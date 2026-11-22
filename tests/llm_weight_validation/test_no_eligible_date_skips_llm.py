import json
from helpers import read_output
def test_no_eligible_date_skips_llm(module13, fake_root):
    p=fake_root/"data/pipeline/12_compute_pws_score/pws_score.json"
    data=json.loads(p.read_text())
    for r in data["records"]:
        r["llm_adjustment_eligible"]=False
    p.write_text(json.dumps(data))
    module13.run(["--enable-llm"], root=fake_root)
    assert read_output(fake_root)["status"] == "skipped_no_eligible_date"
