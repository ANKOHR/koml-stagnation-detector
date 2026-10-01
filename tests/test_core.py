import pytest
from koml_stagnation_detector.core import analyze, InputError
from koml_stagnation_detector.fixtures import generate
from koml_stagnation_detector.cli import read_records

@pytest.fixture
def rows(tmp_path):
    generate(tmp_path)
    return read_records(tmp_path)

@pytest.mark.parametrize("field,value", [("activity_count", -1), ("completed", True), ("evidence", 10**12), ("date", "2027-01-01"), ("project", "x"*10001), ("synthetic", "true"), ("date", "bad"), ("source", "")])
def test_rejects_adversarial_values(rows, field, value):
    rows[0][field] = value
    with pytest.raises(InputError, match=field):
        analyze(rows)

def test_duplicate_ids(rows):
    rows[1]["id"] = rows[0]["id"]
    with pytest.raises(InputError, match="duplicate"):
        analyze(rows)

def test_corrupted_ground_truth_changes_computation(rows):
    before = analyze(rows)
    rows[0]["completed"] += 1
    after = analyze(rows)
    assert after["totals"]["stagnation"] == before["totals"]["stagnation"] - 1
    assert after["totals"]["completed_delta"] == before["totals"]["completed_delta"] + 1

def test_threshold_boundary_and_regression(rows):
    r = rows[0]
    r["activity_count"] = 4
    r["completed"] = 1
    assert analyze([r])["rows"][0]["status"] == "quiet"
    r["activity_count"] = 5
    result = analyze([r])
    assert result["rows"][0]["status"] == "stagnation"
    assert result["totals"]["regressions"] == 1
    r["evidence"] += 1
    assert analyze([r])["rows"][0]["status"] == "progress"

def test_real_provenance(rows):
    rows[0].update(synthetic=False, source="henry_entered")
    assert analyze(rows)["provenance"]["real_henry_entered_records"] == 1
