# Verification Slice V1 Evaluation Report

- Dataset: `engineering_fixture_set` v`1.1.0`
- Generated: 2026-09-02T11:05:28.791960+00:00
- Tasks: 8; hard-verifier coverage: 7; indeterminate: 1
- Shadow waiver coverage: 0.375; observed counterfactual shadow miss rate: 0.0

## Per-checklet results

| Checklet | Findings | Precision | Recall | Unique catches |
| --- | ---: | ---: | ---: | ---: |
| change_scope | 1 | 0.0 | None | 0 |
| dependency_integration_risk | 1 | 1.0 | 1.0 | 1 |
| error_boundary | 1 | 1.0 | 1.0 | 1 |
| requirement_coverage | 1 | 1.0 | 1.0 | 1 |
| test_adequacy | 1 | 0.0 | None | 0 |

## Known limitations

- engineering_fixture_set is not a statistically representative production dataset
- checklet metrics use seeded fixture expectations and should not be generalized beyond this sample
- would_waive is an experimental counterfactual and never authorizes acceptance
- VS-V1.1 uses a conservative shadow policy: any medium-or-higher finding forces would_hard_verify
- hard outcomes for executable fixtures come from CommandHardVerifier, not producer metadata
- per-checklet precision is against hard-verifier rejection; a seeded-defect catch can have precision 0 if independent reference tests still pass
