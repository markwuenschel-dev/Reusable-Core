# VS-V1.2a bug ledger

| ID | Classification | Item | Status |
|---|---|---|---|
| B1 | CONFIRMED BUG | Decision gate mishandles `reject_rate == 0.0` via truthiness | closed in prior wave; regression retained |
| B2 | CONFIRMED BUG | Real-task threshold did not require real ∩ determinate | closed in prior wave; counts/tests expanded this wave |
| B3 | CONFIRMED ISSUE | Baseline hash-checked but not reconstructable from committed source; dirty tree still greened `ok` | this wave: `ok` requires tracked reconstructability |
| B4 | CONFIRMED METHODOLOGY GAP | Shared-primitive adjudicator treated as independent | this wave: labeled `deterministic-shared`; evaluation-grade path required for holdout |
| B5 | SUSPECTED PORTABILITY BUG | Sequential multiprocessing leak/hang on some hosts | stress harness + lifecycle assertions; not claimed hang-proof off supported CI |
| B6 | REQUIREMENTS DISCOVERY | Protected partitions labeled but ordinary analysis still mixed holdout/calibration | prior wave filtered operational scope; this wave persists holdout_state and redacts protected labels |
| B7 | UNRELATED TECHNICAL DEBT | V1.1 runtime still uncommitted vs HEAD `4f929a0` | closed: V1.1 landed at `1a0359e`; baseline hashes Git-canonical LF so `git_commit_match` holds across CRLF checkouts |
