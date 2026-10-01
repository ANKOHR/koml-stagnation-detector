# KOML Stagnation Detector

A CPU-only Python CLI that flags recorded activity without recorded progress.
It uses local files, pure deterministic rules, and no network or language-model calls.

## Quickstart

Requires Python 3.10+ and setuptools. From this repository:

```powershell
python -m pip install --no-deps --no-build-isolation -e .
ksd fixtures --out demo
ksd run --input demo
ksd report --format md
```

For an environment without an installed console script, replace `ksd` with
`python -m koml_stagnation_detector.cli`. Tests: `python -m pytest -q`.
If a user installation puts `ksd.exe` outside PATH, add the Scripts directory
printed by pip to your session PATH, or use the module invocation above.
Pytest is a development prerequisite. Installation above does not fetch dependencies.

A hand-written five-record synthetic input is in `examples/tiny/records.jsonl`:

```powershell
ksd run --input examples/tiny
ksd report --format json
```

## Rule and hypothesis

Hypothesis: explicit activity counts and changes in accepted outcomes/evidence can
support a reproducible review signal. The default activity threshold is five
recorded events within a user-defined review window. At least one positive
completed-outcome or verified-evidence delta means `progress`. With neither
positive delta, activity at or above the threshold means `stagnation`; otherwise
it means `quiet`. Negative deltas are accepted and separately marked as regression.
A positive delta in either metric counts as progress even if the other regresses.
This rule is a review trigger, not a causal diagnosis or a measurement of value.

## Input format reference

Each input directory contains UTF-8 `*.jsonl` files. Every nonblank line is one
object with exactly these fields. Lines starting with `#` are header comments.
The loader sorts filenames and the engine sorts rows by globally unique ID.
`expectations.json` is metadata and is never read as observations. Other JSON,
CSV or YAML files cause a named unsupported-format schema error. Other extensions
are ignored. An empty directory is a valid zero-record dataset.

```json
{"id":"review-001","project":"Henry's project","date":"2026-09-30","as_of":"2026-09-30","synthetic":false,"source":"henry_entered","activity_count":8,"baseline_completed":2,"completed":2,"baseline_evidence":3,"evidence":3}
```

This example is illustrative, not a measured real trial. Henry must enter his own
observations before declaring a record real. Real records require
`synthetic: false` and `source: "henry_entered"`; that declaration cannot be verified
by the tool. Synthetic records require `synthetic: true` and a nonempty source.

| Field | Meaning and validation |
| --- | --- |
| id | Unique review-window ID, nonempty text, maximum 10000 characters |
| project | Project name, same text limits; multiple windows may share a project |
| date | Window end date, strict YYYY-MM-DD |
| as_of | Explicit review reference date, strict YYYY-MM-DD; date must not exceed it |
| synthetic | Boolean provenance label |
| source | Provenance declaration, same text limits |
| activity_count | Events during this window |
| baseline_completed, completed | Accepted outcome counts at window start and end |
| baseline_evidence, evidence | Verified evidence counts at window start and end |

All five counts must be integers from 0 to 1000000000, with booleans rejected.
Unknown fields, missing fields, duplicate IDs, negative counts and invalid dates
are errors, never silently dropped. Future means after supplied `as_of`, not after
the machine clock. Em dash characters are rejected in input text. Unicode and
Windows path strings work; use JSON backslash escaping. Text is limited to prevent
unbounded individual fields; the dataset is read into memory.

Each record is an independently measured window. Totals sum windows, not unique
projects. Use nonoverlapping windows if aggregate event totals are meant to count
unique activity. End counts are not summed as project inventory. Deltas are signed.
Count denominators reconcile: stagnation + progress + quiet = records.

## Subcommands and examples

| Command | Purpose | Example |
| --- | --- | --- |
| fixtures | Write 200 labelled synthetic records and expectations | `ksd fixtures --out demo` |
| run | Parse, validate, compute and atomically save results | `ksd run --input demo --threshold 5 --results .ksd/result.json` |
| report | Validate saved results and render with provenance | `ksd report --format md --out report.md` |
| stalled | Display flagged windows and dataset-wide totals | `ksd stalled --input demo --threshold 5` |
| audit | Show all computed counts, deltas and provenance | `ksd audit --input demo` |

Every command provides `--help` and an example. `run` prints a JSON report and
writes `.ksd/result.json` by default. `report` reads that file unless `--results`
is supplied. Use the same path for both commands when overriding it. Saved
results are recomputed and checked before rendering, so corrupted totals fail.
`stalled` filters displayed rows only; totals and provenance still cover the whole
input. All outputs are deterministic for the same inputs, threshold and format.
No randomness is used, so no seed is required. No runtime timestamp is inserted.

## Architecture

```text
fixtures.py -> labelled local records + independent expectations
local JSONL -> cli.py validation -> core.py pure rules -> saved result JSON
saved result JSON -> recomputation check -> report.py -> Markdown / JSON
```

## Honesty boundary and fixture policy

Every report and computed CLI output states synthetic and declared-real record
counts. Synthetic fixture JSONL starts with a header comment and every record has
`synthetic: true`. The expectations JSON uses `_comment` as its header equivalent
and has `synthetic: true`, because JSON has no comment syntax. The tiny example
follows the same policy. Metadata never supplies the engine's answers.

No discovery, prediction, estimated productivity or claimed savings are provided.
Time and money saved are unmeasured and explicitly marked as such. Hypothetical
or illustrative examples are labelled. Timing in EVIDENCE.md measures execution,
not time saved against a baseline. Precision and recall on planted synthetic
cases validate implementation of the rule, not real-world accuracy. Input labels
and counts are supplied by the operator and can be wrong or gamed.

## Failure modes

Parse errors identify file and physical line (and column for malformed JSON).
Schema errors name file, line and offending field. Unsupported structured file
formats are rejected with a conversion hint. Missing input or saved result names
the path and usage hint. Errors return exit code 2 without tracebacks. Report
writes use a temporary sibling file and atomic replacement, with cleanup on
failure. No partial destination is left behind; an existing report is preserved.
Malformed evidence counts, stale window boundaries or inflated activity can still
produce misleading signals even with valid schema. The tool cannot independently
check evidence quality, attribution, causality or whether a completed outcome is
valuable. No real Henry data has been provided or measured in this build.

## Acceptance evidence and improvement hook

See EVIDENCE.md for measured synthetic results, acceptance criteria, and limits.
After two weeks of real use, hand-check every flagged window and a sample of
unflagged windows, recording TP, FP, TN and FN against an operator's judgment of
activity without meaningful progress. Record sample selection and denominator.
The primary metric is error rate `(FP + FN) / checked_windows`; zero checked
windows means unmeasured. Also record days used and total runs. Keep real trial
inputs and findings private, outside shipped fixtures. No two-week trial has
occurred during this build.

If measured error exceeds 10 percent, fix the most frequent failure cause and
repeat the same hand-check. If unused, record why and kill the project. A candidate
improvement is requiring verified evidence for progress if count inflation causes
false negatives; it is unvalidated and must be driven by real trial evidence.

Verdict is pending the two-week evidence window, not a fabricated decision.
Record the verdict with sample size, dates, usage and reason: expand for daily use
or revenue; integrate for strong sibling overlap; commercialise if a buyer would
pay as-is; maintain as portfolio evidence otherwise; kill if unused or unable to
meet acceptance criteria. See VERDICT.md for the decision record.
