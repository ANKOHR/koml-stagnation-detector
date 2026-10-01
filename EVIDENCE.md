# Build evidence

Measured locally on 2026-10-01 with Python 3.12.10, Windows, CPU only.
`python -m pytest -q`: 38 tests passed. The installed `ksd.exe` entry point was
also executed as three fresh processes, not just called in-process.

- Synthetic end-to-end fixtures/run/report: 0.603114 seconds (under 5 seconds).
- Synthetic `ksd report --format json`: 0.221179 seconds (under 5 seconds).
- Synthetic records: 200. Flagged planted windows: 40 of 40.
- Synthetic false positives: 0. False negatives: 0.
- Synthetic activity events: 1200; completed delta: 120; evidence delta: 240.
- Synthetic progress windows: 120; quiet windows: 40; regressions: 0.
- Every report total matched the independent hand-computed expectations exactly.

Hand calculation: 40 busy unchanged windows at 10 activity events, 120 progress
windows at 6 events, 40 quiet unchanged windows at 2 events. Activity total is
400 + 720 + 80 = 1200. Progress windows each add one completed outcome and two
evidence items, giving deltas 120 and 240. IDs window-000 through window-039 are
the planted stagnation set. Metadata is excluded from input computation.

The five hand-written synthetic windows separately produce 2 stagnation signals,
2 progress signals, 1 quiet signal, 1 regression, 26 activity events, completed
delta 0 and evidence delta 1. This tests cancellation of signed deltas.

Acceptance checks cover byte-identical repeat output, empty directories, malformed
JSON and invalid UTF-8 with physical line diagnostics, schema drift, duplicate IDs,
negative/oversized/boolean counts, future dates relative to explicit review date,
Unicode and long fields, Windows path strings, report provenance, zero fabricated
savings, threshold boundaries and atomic report write failures. Deliberately
changing a planted record changes report totals. Changing only saved totals is
rejected. No em dash characters were found in source, tests, docs or demo output.

These timings measure execution only, not time or money saved. Ground-truth
accuracy here is synthetic rule accuracy, not real-world effectiveness. No real
trial was conducted. The two-week metric and final verdict remain pending.
Publishing was not performed; it belongs to the separate verification step.
