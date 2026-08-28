# Verification Slice V1 Evaluation Report

- Dataset: `engineering_fixture_set` v`1.0.0`
- Generated: 2026-08-28T10:40:21.691267+00:00
- Tasks: 8; hard-verifier coverage: 7; indeterminate: 1
- Shadow waiver coverage: 0.875; observed counterfactual shadow miss rate: 0.5714285714285714

## Per-checklet results

| Checklet | Findings | Precision | Recall | Unique catches |
| --- | ---: | ---: | ---: | ---: |
| change_scope | 1 | 1.0 | 1.0 | 1 |
| dependency_integration_risk | 1 | 1.0 | 1.0 | 1 |
| error_boundary | 1 | 1.0 | 1.0 | 1 |
| requirement_coverage | 1 | 1.0 | 1.0 | 1 |
| test_adequacy | 1 | 1.0 | 1.0 | 1 |

## Known limitations

- engineering_fixture_set is not a statistically representative production dataset
- checklet metrics use seeded fixture expectations and should not be generalized beyond this sample
- would_waive is an experimental counterfactual and never authorizes acceptance
