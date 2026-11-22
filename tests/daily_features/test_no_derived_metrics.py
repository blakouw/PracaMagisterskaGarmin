from helpers07 import setup_root, run_module, output
FORBIDDEN = {"rhr_delta","ln_rmssd","acute_load","chronic_load","acwr","acwr_ewma","monotony","strain","readiness","LQ","REC","CAP","VS","pws_score","pws_weights"}
def test_no_forbidden_fields_in_feature_table(tmp_path):
    root = setup_root(tmp_path)
    assert run_module(root) == 0
    fields = set(output(root)["fields"])
    assert not (fields & FORBIDDEN)
