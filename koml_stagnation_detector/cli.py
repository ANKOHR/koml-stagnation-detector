"""Local-only command interface. No network or model calls."""
import argparse
import json
import os
from pathlib import Path
import tempfile
from .core import InputError, analyze
from .fixtures import generate
from .report import render

def read_records(directory):
    directory = Path(directory)
    if not directory.is_dir():
        raise InputError(f"MissingInput: {directory}: use --input with an existing directory")
    unsupported = sorted(path for path in directory.iterdir()
                         if path.suffix.lower() in (".json", ".csv", ".yaml", ".yml")
                         and path.name != "expectations.json")
    if unsupported:
        raise InputError(f"SchemaError: {unsupported[0]}: line 1, field format: only JSONL input is supported; use records.jsonl")
    records = []
    locations = []
    for path in sorted(directory.glob("*.jsonl")):
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeError as exc:
            raw = path.read_bytes()
            line = raw[:exc.start].count(b"\n") + 1
            raise InputError(f"ParseError: {path}: line {line}: invalid UTF-8") from exc
        for line, text in enumerate(content.splitlines(), 1):
            if not text.strip() or text.startswith("#"):
                continue
            try:
                records.append(json.loads(text))
                locations.append((path, line))
            except json.JSONDecodeError as exc:
                raise InputError(f"ParseError: {path}: line {line}, column {exc.colno}: {exc.msg}") from exc
    # Validate individually for precise physical line diagnostics, then together for duplicates.
    from .core import validate
    seen = set()
    for record, (path, line) in zip(records, locations):
        try:
            validate([record])
            if record["id"] in seen:
                raise InputError("SchemaError: field id: duplicate id")
            seen.add(record["id"])
        except InputError as exc:
            raise InputError(f"{path}: line {line}: {exc}") from exc
    return records

def atomic_write(path, content):
    path = Path(path)
    temporary = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(content)
        os.replace(temporary, path)
    except OSError as exc:
        raise InputError(f"ReportWriteError: {path}: {exc}") from exc
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()

def main(argv=None):
    parser = argparse.ArgumentParser(description="Compute activity-without-progress signals from local JSONL.")
    sub = parser.add_subparsers(dest="command", required=True)
    f = sub.add_parser("fixtures", help="Generate 200 labelled synthetic records", epilog="Example: ksd fixtures --out demo")
    f.add_argument("--out", required=True)
    for name, help_text in (("run", "Analyze and persist computed results"), ("stalled", "List windows flagged for stagnation"), ("audit", "Validate inputs and show reconciled counts")):
        s = sub.add_parser(name, help=help_text, description=help_text, epilog=f"Example: ksd {name} --input demo")
        s.add_argument("--input", required=True)
        s.add_argument("--threshold", type=int, default=5)
        if name == "run":
            s.add_argument("--results", default=".ksd/result.json")
    r = sub.add_parser("report", help="Render computed results with provenance", epilog="Example: ksd report --format md")
    r.add_argument("--format", choices=("md", "json"), default="md")
    r.add_argument("--results", default=".ksd/result.json")
    r.add_argument("--out")
    args = parser.parse_args(argv)
    try:
        if args.command == "fixtures":
            generate(args.out)
            print("Generated 200 synthetic records and synthetic hand-computed expectations.")
        elif args.command == "report":
            path = Path(args.results)
            if not path.is_file():
                raise InputError(f"MissingInput: {path}: run ksd run --input <dir> first")
            try:
                result = json.loads(path.read_text(encoding="utf-8"))
                recomputed = analyze(result["rows"] and [{k: v for k, v in row.items() if k not in ("status", "regression", "completed_delta", "evidence_delta")} for row in result["rows"]], result["threshold"])
                if recomputed != result:
                    raise InputError(f"SchemaError: {path}: stored results do not reconcile")
            except json.JSONDecodeError as exc:
                raise InputError(f"ParseError: {path}: line {exc.lineno}: {exc.msg}") from exc
            except (KeyError, TypeError, AttributeError) as exc:
                raise InputError(f"SchemaError: {path}: invalid results fields: {exc}") from exc
            output = render(result, args.format)
            if args.out:
                atomic_write(args.out, output)
            else:
                print(output, end="")
        else:
            result = analyze(read_records(args.input), args.threshold)
            if args.command == "run":
                atomic_write(args.results, json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
                print(render(result, "json"), end="")
            elif args.command == "audit":
                print(render(result, "json"), end="")
            else:
                result = dict(result, rows=[r for r in result["rows"] if r["status"] == "stagnation"])
                print(render(result), end="")
        return 0
    except (InputError, OSError, UnicodeError) as exc:
        import sys
        print(str(exc).replace("\u2014", "-"), file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
