import json
from koml_stagnation_detector.fixtures import generate
from koml_stagnation_detector.cli import read_records
from koml_stagnation_detector.core import analyze

def test_fixtures_labelled_synthetic(tmp_path):
    generate(tmp_path)
    assert (tmp_path / "records.jsonl").read_text().startswith("# Synthetic")
    assert all(r["synthetic"] is True for r in read_records(tmp_path))
    expected = json.loads((tmp_path / "expectations.json").read_text())
    assert expected["synthetic"] is True
    assert "Synthetic" in expected["_comment"]

def test_fixture_ground_truth_matches_hand_computed(tmp_path):
    generate(tmp_path)
    result = analyze(read_records(tmp_path))
    expected = json.loads((tmp_path / "expectations.json").read_text())
    assert result["totals"] == expected["totals"]
    assert result["totals"] == dict(records=200, activity_count=1200, completed_delta=120, evidence_delta=240, stagnation=40, progress=120, quiet=40, regressions=0)
    assert [r["id"] for r in result["rows"] if r["status"] == "stagnation"] == expected["stagnation_ids"]
