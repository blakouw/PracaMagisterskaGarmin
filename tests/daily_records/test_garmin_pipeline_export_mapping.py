from __future__ import annotations

import datetime
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "gathering_data" / "token_setup.py"


def load_exporter():
    spec = importlib.util.spec_from_file_location("garmin_pipeline_export", SOURCE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class FakeGarminApi:
    def get_daily_steps(self, *_args):
        return []

    def get_body_composition(self, *_args):
        return []

    def get_activities_by_date(self, *_args):
        return [{"activityId": 123, "startTimeLocal": "2026-08-21T10:00:00", "duration": 3600}]

    def get_activity(self, activity_id):
        assert activity_id == "123"
        return {"summaryDTO": {"directWorkoutRpe": 60, "directWorkoutFeel": 50}}

    def get_user_summary(self, _date):
        return {
            "activeKilocalories": 100,
            "restingHeartRate": 50,
            "lastSevenDaysAvgRestingHeartRate": 52,
        }

    def get_stats(self, _date):
        return {}

    def get_stats_and_body(self, _date):
        return {}

    def get_sleep_data(self, _date):
        return {"dailySleepDTO": {"averageSpO2Value": 96, "lowestSpO2Value": 88}}

    def get_hrv_data(self, _date):
        return {}

    def get_stress_data(self, _date):
        return {}

    def get_respiration_data(self, _date):
        return {}

    def get_spo2_data(self, _date):
        return {
            "averageSpO2": 97,
            "lowestSpO2": 87,
            "lastSevenDaysAvgSpO2": 96,
            "avgSleepSpO2": 95,
        }


def test_pipeline_export_maps_rhr_baseline_and_sleep_spo2() -> None:
    exporter = load_exporter()
    date = datetime.date(2026, 8, 21)

    rows, errors = exporter._build_pipeline_workbook_rows(FakeGarminApi(), date, date)

    assert errors == []
    assert rows["Daily_RHR"][0]["restingHeartRate"] == 50
    assert rows["Daily_RHR"][0]["baselineRestingHeartRate"] == 52
    assert rows["Daily_SpO2"][0]["avgSleepSpo2"] == 95
    assert rows["Daily_SpO2"][0]["sevenDayAvgSpo2"] == 96
    assert rows["Daily_Sleep"][0]["averageSpo2"] == 95
    assert rows["Activities"][0]["directWorkoutRpe"] == 60
    assert rows["Activities"][0]["directWorkoutFeel"] == 50
    assert rows["Activities"][0]["directWorkoutRpe"] == 60
    assert rows["Activities"][0]["directWorkoutFeel"] == 50
