# Lessons for KOML

Activity is a window count; progress needs explicit start/end observations and
operator-defined accepted outcomes. A detector cannot infer value from busyness.
A progress delta in either outcome or evidence can coexist with regression in the
other metric, so regressions must stay visible independently of the signal.

Validated by synthetic evidence: pure rules recover the planted 40 stagnation
windows exactly and preserve all count totals. Mutation of a planted record
changes computed totals, which rejects the assumption that fixture matching alone
proves a working detector. Real-world usefulness remains unvalidated.

Operating rule for future builds: pin input semantics and the reference date,
keep planted labels outside the computation, and require a private hand-checked
trial before claiming real-world accuracy or saved time.

Build improvement from evidence: a stored-result tampering test showed why reports
need to recompute their totals before rendering. The report now rejects inconsistent
saved results with a named schema error. This guards stored-result integrity; it
does not authenticate the original observations. The separate two-week improvement
hook remains pending real use.
