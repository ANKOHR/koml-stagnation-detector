import json
from koml_stagnation_detector.core import analyze
from koml_stagnation_detector.report import render
from koml_stagnation_detector.fixtures import generate
from koml_stagnation_detector.cli import read_records

def result(tmp_path):
    generate(tmp_path)
    return analyze(read_records(tmp_path))

def test_report_matches_ground_truth_exact(tmp_path):
    r = result(tmp_path)
    expected = json.loads((tmp_path / "expectations.json").read_text())
    assert json.loads(render(r, "json"))["totals"] == expected["totals"]
    for key, value in expected["totals"].items():
        assert f"| {key} | {value} |" in render(r)

def test_report_zero_false_positives(tmp_path):
    r = json.loads(render(result(tmp_path), "json"))
    planted = {f"window-{i:03}" for i in range(40)}
    found = {row["id"] for row in r["rows"] if row["status"] == "stagnation"}
    assert found == planted

def test_report_carries_provenance_banner(tmp_path):
    for fmt in ("md", "json"):
        output = render(result(tmp_path), fmt)
        assert "200 synthetic fixture records" in output
        assert "0 real records" in output

def test_hypothetical_figures_labelled():
    output = render(analyze([]))
    assert "Time and money saved: unmeasured; no savings claimed" in output

def test_no_em_dashes_in_outputs(tmp_path):
    for fmt in ("md", "json"):
        assert "\u2014" not in render(result(tmp_path), fmt)

def test_handles_unicode_and_long_inputs(tmp_path):
    generate(tmp_path)
    rows = read_records(tmp_path)
    rows[0]["project"] = "研究 café C:\\work\\项目 | <tag>\n" + "a"*9000
    r = analyze(rows)
    assert json.loads(render(r, "json"))["rows"][0]["project"] == rows[0]["project"]
    assert "研究" in render(r)
    assert "&#124;" in render(r)
