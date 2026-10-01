import json
import time
import pytest
from koml_stagnation_detector.cli import main

def test_run_completes_on_fixture(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    start = time.perf_counter()
    assert main(["fixtures", "--out", "demo"]) == 0
    assert main(["run", "--input", "demo"]) == 0
    assert main(["report", "--format", "md"]) == 0
    assert time.perf_counter() - start < 5
    assert "Data provenance:" in capsys.readouterr().out

def test_empty_input_renders_without_traceback(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["run", "--input", "."]) == 0
    assert main(["report"]) == 0
    assert "| records | 0 |" in capsys.readouterr().out

def test_malformed_input_named_error(tmp_path, capsys):
    (tmp_path / "broken.jsonl").write_text('# header\n{"broken":\n')
    assert main(["run", "--input", str(tmp_path)]) == 2
    error = capsys.readouterr().err
    assert "ParseError" in error and "broken.jsonl" in error and "line 2" in error

def test_determinism_byte_identical(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    main(["fixtures", "--out", "demo"])
    main(["run", "--input", "demo"])
    first = (tmp_path / ".ksd/result.json").read_bytes()
    main(["run", "--input", "demo"])
    assert first == (tmp_path / ".ksd/result.json").read_bytes()
    main(["report", "--out", "a.md"])
    main(["report", "--out", "b.md"])
    assert (tmp_path / "a.md").read_bytes() == (tmp_path / "b.md").read_bytes()

@pytest.mark.parametrize("command", ["fixtures", "run", "report", "stalled", "audit"])
def test_cli_smoke_all_subcommands(command, tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc:
        main([command, "--help"])
    assert exc.value.code == 0
    assert "Example:" in capsys.readouterr().out
    main(["fixtures", "--out", "demo"])
    main(["run", "--input", "demo"])
    args = [command, "--out", "more"] if command == "fixtures" else [command] if command == "report" else [command, "--input", "demo"]
    assert main(args) == 0

def test_missing_input(tmp_path, capsys):
    assert main(["run", "--input", str(tmp_path / "absent")]) == 2
    assert "MissingInput" in capsys.readouterr().err

def test_schema_error_names_file_line_field(tmp_path, capsys):
    (tmp_path / "bad.jsonl").write_text('{}\n')
    assert main(["audit", "--input", str(tmp_path)]) == 2
    error = capsys.readouterr().err
    assert "SchemaError" in error and "bad.jsonl" in error and "line 1" in error and "fields" in error

def test_report_write_failure_no_partial(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    main(["run", "--input", "."])
    (tmp_path / "blocked").write_text("original")
    before = set(tmp_path.iterdir())
    assert main(["report", "--out", "blocked/out.md"]) == 2
    assert "ReportWriteError" in capsys.readouterr().err
    assert (tmp_path / "blocked").read_text() == "original"
    assert set(tmp_path.iterdir()) == before

def test_tampered_results_rejected(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    main(["run", "--input", "."])
    path = tmp_path / ".ksd/result.json"
    r = json.loads(path.read_text())
    r["totals"]["records"] = 900
    path.write_text(json.dumps(r))
    assert main(["report"]) == 2
    assert "do not reconcile" in capsys.readouterr().err

@pytest.mark.parametrize("suffix", ["json", "csv", "yaml"])
def test_unsupported_format_named_error(tmp_path, capsys, suffix):
    (tmp_path / f"bad.{suffix}").write_text("malformed")
    assert main(["audit", "--input", str(tmp_path)]) == 2
    assert "SchemaError" in capsys.readouterr().err

def test_invalid_utf8_named_error(tmp_path, capsys):
    (tmp_path / "bad.jsonl").write_bytes(b"# header\n\xff")
    assert main(["audit", "--input", str(tmp_path)]) == 2
    error = capsys.readouterr().err
    assert "ParseError" in error and "line 2" in error

def test_five_record_hand_written_input():
    from pathlib import Path
    from koml_stagnation_detector.cli import read_records
    from koml_stagnation_detector.core import analyze
    input_path = Path(__file__).resolve().parents[1] / "examples/tiny"
    assert analyze(read_records(input_path))["totals"] == dict(records=5, activity_count=26, completed_delta=0, evidence_delta=1, stagnation=2, progress=2, quiet=1, regressions=1)
