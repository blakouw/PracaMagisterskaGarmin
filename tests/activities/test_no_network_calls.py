from activity_helpers import ROOT
def test_no_network_calls():
 text=(ROOT/"pipeline/06_normalize_activities/main.py").read_text(encoding="utf-8")
 assert "requests" not in text; assert "urllib" not in text; assert "garminconnect" not in text
