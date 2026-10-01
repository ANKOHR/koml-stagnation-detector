"""Pure computations. Signals are rule-based, never estimated outcomes."""
from datetime import date

class InputError(ValueError):
    """Named input validation failure."""

FIELDS = {"id", "project", "date", "as_of", "synthetic", "source", "activity_count",
          "baseline_completed", "completed", "baseline_evidence", "evidence"}
COUNTS = ("activity_count", "baseline_completed", "completed", "baseline_evidence", "evidence")

def validate(records):
    seen = set()
    for index, r in enumerate(records, 1):
        def fail(field, reason):
            raise InputError(f"SchemaError: record {index}, field {field}: {reason}")
        if not isinstance(r, dict):
            fail("record", "expected object")
        if set(r) != FIELDS:
            fail("fields", f"missing={sorted(FIELDS-set(r))}, unknown={sorted(set(r)-FIELDS)}")
        for field in ("id", "project", "source"):
            if not isinstance(r[field], str) or not r[field].strip() or len(r[field]) > 10000:
                fail(field, "expected nonempty text up to 10000 characters")
            if "\u2014" in r[field]:
                fail(field, "em dash is forbidden; use a hyphen")
        if r["id"] in seen:
            fail("id", "duplicate id")
        seen.add(r["id"])
        if type(r["synthetic"]) is not bool:
            fail("synthetic", "expected boolean")
        if not r["synthetic"] and r["source"] != "henry_entered":
            fail("source", "real records must declare henry_entered")
        for field in COUNTS:
            if type(r[field]) is not int or not 0 <= r[field] <= 1000000000:
                fail(field, "expected integer between 0 and 1000000000")
        for field in ("date", "as_of"):
            try:
                if not isinstance(r[field], str) or date.fromisoformat(r[field]).isoformat() != r[field]:
                    fail(field, "expected YYYY-MM-DD")
            except (ValueError, TypeError):
                fail(field, "expected YYYY-MM-DD")
        if r["date"] > r["as_of"]:
            fail("date", "future date relative to explicit as_of")
    return records

def analyze(records, threshold=5):
    if type(threshold) is not int or threshold < 1:
        raise InputError("SchemaError: threshold must be a positive integer")
    validate(records)
    rows = []
    for r in sorted(records, key=lambda r: r["id"]):
        completed_delta = r["completed"] - r["baseline_completed"]
        evidence_delta = r["evidence"] - r["baseline_evidence"]
        status = ("progress" if completed_delta > 0 or evidence_delta > 0 else
                  "stagnation" if r["activity_count"] >= threshold else "quiet")
        rows.append(dict(r, completed_delta=completed_delta, evidence_delta=evidence_delta,
                         status=status, regression=completed_delta < 0 or evidence_delta < 0))
    return {"schema_version": 1, "threshold": threshold,
            "provenance": {"synthetic_records": sum(r["synthetic"] for r in records),
                           "real_henry_entered_records": sum(not r["synthetic"] for r in records)},
            "totals": {"records": len(rows), "activity_count": sum(r["activity_count"] for r in rows),
                       "completed_delta": sum(r["completed_delta"] for r in rows),
                       "evidence_delta": sum(r["evidence_delta"] for r in rows),
                       **{s: sum(r["status"] == s for r in rows) for s in ("stagnation", "progress", "quiet")},
                       "regressions": sum(r["regression"] for r in rows)},
            "honesty": "Computed from supplied counts only. Rule-based signals, not proof of project value. Time and money saved: unmeasured; no savings claimed.",
            "rows": rows}
