from activity_helpers import base_row, copy_policy, out, read_json, run, write_activities_csv


def test_garmin_rpe_is_normalized_and_missing_value_stays_null(module06, case_root):
    copy_policy(case_root)
    write_activities_csv(
        case_root,
        [
            base_row(activityId="100", directWorkoutRpe="60", directWorkoutFeel="50"),
            base_row(activityId="101", directWorkoutRpe="", directWorkoutFeel=""),
        ],
    )

    assert run(module06, case_root) == 0
    records = read_json(out(case_root) / "activities_normalized.json")["activities"]
    by_id = {record["activity_id"]: record for record in records}

    assert by_id["100"]["perceived_effort_rpe"] == 6.0
    assert by_id["100"]["subjective_feeling_score"] == 50
    assert by_id["101"]["perceived_effort_rpe"] is None
    assert by_id["101"]["subjective_feeling_score"] is None
