"""Deterministic reports with explicit provenance."""
import json

def render(result, format="md"):
    p = result["provenance"]
    banner = (f"Data provenance: {p['synthetic_records']} synthetic fixture records; "
              f"{p['real_henry_entered_records']} real records declared as Henry's own hand-entered data (not independently verified).")
    if format == "json":
        return json.dumps(dict(result, provenance_banner=banner), ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if format != "md":
        raise ValueError("ReportError: unsupported format")
    lines = ["# KOML Stagnation Detector", "", banner, "", result["honesty"], "",
             f"Activity threshold: {result['threshold']} recorded events per review window.", "",
             "| Computed metric | Value |", "| --- | ---: |"]
    lines += [f"| {k} | {v} |" for k, v in result["totals"].items()]
    lines += ["", "## Review windows", "", "| ID | Project | Activity | Completed delta | Evidence delta | Signal | Regression |", "| --- | --- | ---: | ---: | ---: | --- | --- |"]
    def escape(s):
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("|", "&#124;").replace("\n", " ").replace("\r", " ")
    lines += [f"| {escape(r['id'])} | {escape(r['project'])} | {r['activity_count']} | {r['completed_delta']} | {r['evidence_delta']} | {r['status']} | {r['regression']} |" for r in result["rows"]]
    return "\n".join(lines) + "\n"
