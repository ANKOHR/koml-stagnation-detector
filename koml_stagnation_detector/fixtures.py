"""Synthetic fixtures; no randomness and no inferred ground truth."""
import json
from pathlib import Path

# Hand-computed: 40*10 + 120*6 + 40*2 = 1200 activity events.
# Progress: 120 windows each add one completed outcome and two evidence items.
EXPECTATIONS = {"synthetic": True, "_comment": "Synthetic hand-computed expectations",
                "totals": {"records": 200, "activity_count": 1200, "completed_delta": 120,
                           "evidence_delta": 240, "stagnation": 40, "progress": 120,
                           "quiet": 40, "regressions": 0},
                "stagnation_ids": [f"window-{i:03}" for i in range(40)]}

def generate(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for i in range(200):
        progress = 40 <= i < 160
        rows.append({"id": f"window-{i:03}", "project": f"Synthetic project {i:03}",
                     "date": "2026-09-30", "as_of": "2026-09-30", "synthetic": True,
                     "source": "synthetic_fixture", "activity_count": 10 if i < 40 else 6 if progress else 2,
                     "baseline_completed": 2, "completed": 3 if progress else 2,
                     "baseline_evidence": 3, "evidence": 5 if progress else 3})
    (out / "records.jsonl").write_text("# Synthetic labelled fixture records\n" + "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
    (out / "expectations.json").write_text(json.dumps(EXPECTATIONS, indent=2, sort_keys=True) + "\n", encoding="utf-8")
