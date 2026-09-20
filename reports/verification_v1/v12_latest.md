# VS-V1.2 Real-Task Evidence Report

## Executive conclusion

**Decision:** `COLLECT_MORE_V1_2_DATA`

- real determinate tasks: 0 / 50 minimum

### Blocking gates

- `real_determinate_sample`: {'name': 'real_determinate_sample', 'passed': False, 'observed': 0, 'required': 50}
- `diversity`: {'name': 'diversity', 'passed': False, 'observed': {'n_repositories': 0, 'n_task_families': 0, 'n_patch_sizes': 0}, 'required': {'n_repositories': 2, 'n_task_families': 2, 'n_patch_sizes': 2}}

### Passing gates

- `integrity`

- Decision gate: `v12-decision-gate-1.1` (research heuristic)

- Experiment: `vs-v1.2-exp-001` cohort `v1.2-c01-v11-frozen`
- Baseline: `vs-v1.1-baseline-001` `19ab491a0e0b852362f74c69329e455b23bbd663d4adf4f42e5636501f7014b6`
- Dataset: `vs-v1.2-metric-integrity` v`1.2.0` split `grouped-sha256-v1/vs-v1.2-split-seed-001`
- Analysis scope: `operational`
- Holdout state: `sealed`
- Calibration state: `sealed`
- Protected partitions: {'development': 'visible', 'policy_selection': 'visible', 'calibration_reserved': 'sealed', 'holdout': 'sealed'}
- Sealed partition counts (no outcome labels): {'holdout': 0, 'calibration_reserved': 0}
- Baseline reconstructability: see validate-baseline (`content_match` / `source_reconstructable` / `git_commit_match`)
- Adjudication modes: {'shared_deterministic': 'deterministic-shared', 'independent_deterministic': 'independent-ast-inspector', 'expert_blind': 'bounded-expert-review', 'expert_assisted': 'bounded-expert-review/assisted'}
- Isolation: sequential fixture evaluation must leave no child workers; hosted Linux semaphore warnings remain environment-specific
- Git revision: `46768d8ac3ea980127adfb957574ba303c3a2841`
- Analysis code: `sha256:80036f4be87dafee`

## Dataset composition

- N total: 8
- N real: 0
- N real determinate: 0
- N controlled/synthetic: 8
- N determinate: 7
- N accepted: 4
- N rejected: 3
- N unknown: 1
- N infrastructure error: 0
- Repositories: repo-a
- Task families: 8
- Producer families: executor-a
- Patch sizes: {'small': 8}
- Oracle types: unit_reference_tests
- Partition sizes: {'development': 8}

## Data-quality status

- Validator ok: `True`
- Blocking failures: none
- Quality flags: [{'record_id': 'v12_92c3e9c5f4b55c01b3d4d8336d741d4b', 'codes': ['HARD_VERIFY_UNKNOWN']}]

## Hard-verifier outcomes

- `accepted`: 4
- `rejected`: 3
- `outcome_unknown`: 1
- `infrastructure_error`: 0

## Criterion-level checklet quality

| Checklet | N applicable | N adjudicated | N indeterminate | Precision | Recall | FPR | FNR | Abstention | Unique criterion catches | P(reject\|clean) | P(reject\|finding) | Lift | Mean cost | p95 latency |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| requirement_coverage | 8 | 0 | 8 | 0 / 0 (undefined) | 0 / 0 (undefined) | 0 / 0 (undefined) | 0 / 0 (undefined) | n/a | 0 | 1 / 3 | 2 / 4 | 0.1667 | 0.0 | 1.0 |
| test_adequacy | 8 | 0 | 8 | 0 / 0 (undefined) | 0 / 0 (undefined) | 0 / 0 (undefined) | 0 / 0 (undefined) | n/a | 0 | 3 / 6 | 0 / 1 | -0.5000 | 0.0 | 1.0 |
| change_scope | 8 | 0 | 8 | 0 / 0 (undefined) | 0 / 0 (undefined) | 0 / 0 (undefined) | 0 / 0 (undefined) | n/a | 0 | 3 / 7 | 0 / 0 | n/a | 0.0 | 1.0 |
| dependency_integration_risk | 8 | 0 | 8 | 0 / 0 (undefined) | 0 / 0 (undefined) | 0 / 0 (undefined) | 0 / 0 (undefined) | n/a | 0 | 3 / 7 | 0 / 0 | n/a | 0.0 | 1.0 |
| error_boundary | 8 | 0 | 8 | 0 / 0 (undefined) | 0 / 0 (undefined) | 0 / 0 (undefined) | 0 / 0 (undefined) | n/a | 0 | 3 / 7 | 0 / 0 | n/a | 0.0 | 1.0 |

Criterion metrics measure whether each checklet detects its declared criterion.
Hard-outcome metrics measure association with independent verifier rejection, not criterion correctness.

## Hard-outcome predictive utility

Predictive lift is an observational association, not a causal claim.

- `requirement_coverage` unique hard-reject signals: 2; relative lift: 1.5
- `test_adequacy` unique hard-reject signals: 0; relative lift: 0.0
- `change_scope` unique hard-reject signals: 0; relative lift: None
- `dependency_integration_risk` unique hard-reject signals: 0; relative lift: None
- `error_boundary` unique hard-reject signals: 0; relative lift: None

## Objective-gate baseline

- Hard rejection after objective gates pass: 3 / 7 interval [0.1582, 0.7495] (wilson_95)
- Hard rejection after gates pass + all checklets clean: 1 / 2 interval [0.0945, 0.9055] (wilson_95)

## Cross-checklet dependence

- Jaccard overlap: {'requirement_coverage|test_adequacy': 0.0, 'requirement_coverage|change_scope': 0.0, 'requirement_coverage|dependency_integration_risk': 0.0, 'requirement_coverage|error_boundary': 0.0, 'test_adequacy|change_scope': 0.0, 'test_adequacy|dependency_integration_risk': 0.0, 'test_adequacy|error_boundary': 0.0, 'change_scope|dependency_integration_risk': None, 'change_scope|error_boundary': None, 'dependency_integration_risk|error_boundary': None}
- Phi correlation: {'requirement_coverage|test_adequacy': -0.3779644730092272, 'requirement_coverage|change_scope': None, 'requirement_coverage|dependency_integration_risk': None, 'requirement_coverage|error_boundary': None, 'test_adequacy|change_scope': None, 'test_adequacy|dependency_integration_risk': None, 'test_adequacy|error_boundary': None, 'change_scope|dependency_integration_risk': None, 'change_scope|error_boundary': None, 'dependency_integration_risk|error_boundary': None}

## Low-risk-region analysis

- Definition: objective gates pass + no required checklet abstain/error + no medium/high/critical findings
- N: 2; coverage: 0.2857142857142857
- Rejects: 1 / 2 interval [0.0945, 0.9055] (wilson_95)
- Strata: repos={'repo-a': 2} types={'bug_fix': 2} producers={'executor-a': 2} sizes={'small': 2}
- Robustness: low-risk region not demonstrated to generalize

## Shadow-policy counterfactual metrics

- N total / determinate / unknown / infra: 8 / 7 / 1 / 0
- Would waive: 3 (determinate 2)
- False shadow waives: 1 / 2
- Shadow waiver coverage: 0.375
- Observed miss rate: 0.5 interval [0.0945, 0.9055] (wilson_95)
- Would hard-verify: 5
- Unnecessary shadow verifies: 3 / 5

## Stratified results

### repository

- `repo-a`: 3 / 7 (descriptive only)

### task_type

- `bug_fix`: 3 / 7 (descriptive only)

### patch_size_bucket

- `small`: 3 / 7 (descriptive only)

### producer

- `executor-a`: 3 / 7 (descriptive only)

### oracle_type

- `unit_reference_tests`: 3 / 7 (descriptive only)

## Cost/latency

- Gate latency mean ms: 0.5
- Checklet bundle latency mean ms: 1.0
- Hard-verifier latency mean ms: 2.0
- Counterfactual selective-verification economics: NOT REALIZED / NOT AUTHORIZED

## Unknown/infrastructure outcomes

- Unknown: 1 rate=0.125
- Infrastructure error: 0 rate=0.0

## Limitations

- V1.2 is observational/selective-prediction evidence; predictive lift is not causality
- engineering fixtures and controlled mutations are not a substitute for 50-200 real tasks
- unknown and infrastructure-error outcomes are excluded from miss-rate denominators
- would_waive never authorizes acceptance; selective verification remains off
- small-N strata are descriptive only
- V2 criterion metrics use evaluation-grade labels only; shared-primitive inspection is secondary
- default analysis excludes calibration_reserved and holdout until finalize-holdout

## V2 decision gate

`COLLECT_MORE_V1_2_DATA`

- real determinate tasks: 0 / 50 minimum

This decision does not authorize production selective verification or V2 model training.
