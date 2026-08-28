# Verification Slice V1

Verification Slice V1 (VS-V1) is a production-shaped experimental vertical slice for measuring whether narrow diagnostic coding checklets provide useful evidence about independent hard-verifier outcomes. It is not a selective-verification production system.

## Purpose and non-goals

VS-V1 runs a candidate artifact through objective gates and five narrow coding checklets, records a deterministic counterfactual shadow action, then invokes the configured hard verifier for that exact artifact. It produces replayable telemetry and fixture metrics for future research.

VS-V1 does not waive hard verification, approve releases, issue certificates, train a risk model, revise candidate code, route models, or make any claim about a bounded/certified miss rate. `would_waive` means only that the frozen rule policy would have selected that counterfactual action; it never means accepted.

## Runtime flow

```text
candidate bytes -> SHA-256 registration -> objective gates -> diagnostic checklets
    -> rule-based shadow assessment -> mandatory hard verifier -> comparison -> JSONL/events/report
```

`VerificationRunner.run()` owns this sequence. The hard-verifier call is unconditional after gate/checklet observation, and `VerificationRun.final_outcome` is derived only from `HardVerifierResult`. `accepted`, `rejected`, `outcome_unknown`, and `infrastructure_error` remain distinct.

## Artifact identity and contracts

`ArtifactStore` canonicalizes textual line endings and computes SHA-256 over the exact candidate bytes. The resulting `ArtifactRef` contains ID, digest, type, digest-derived version, run ID, timestamp, and metadata. Gates, observations, shadow assessments, hard-verifier results, comparison records, and telemetry all bind that digest. A content change gets a new digest and version; VS-V1 never mutates a registered artifact.

Contracts are frozen dataclasses in `verification_v1/contracts.py`: `ArtifactRef`, `GateResult`, `CheckletSpec`, `CheckletObservation`, `ShadowRiskAssessment`, `HardVerifierResult`, and `ShadowComparison`. Structured mapping output is accepted only when every required checklet-observation field is present, type-compatible, and bound to the issuing checklet/version and artifact digest. Malformed output becomes `verdict=error`.

## Coding domain pack and checklets

The core runner receives gates/checklets through `CodingDomainPack`, not through coding-specific runner logic. The initial domain pack includes these deterministic, diagnostic-only checklets:

- requirement coverage;
- producer test adequacy;
- change scope;
- dependency/integration risk;
- error/boundary handling.

Each checklet has a version, explicit timeout, evidence-family ID, cost record, and `diagnostic` authority ceiling. Checklets receive a disposable copy of artifact metadata and never receive the hard-verifier outcome, fixture label, or another checklet’s result. A timeout, unavailable required context, exception, or malformed output is an explicit typed error; it cannot become clean evidence.

To add a checklet, implement the checklet protocol, give it a new versioned `CheckletSpec` with `authority_ceiling="diagnostic"`, register it in the coding domain pack manifest and default factory, add clean/defect fixtures showing its intended narrow criterion, and run the full fixture evaluation. Do not give it any path to accept, reject, rewrite, or skip hard verification.

## Shadow policy and hard verifier

`ShadowAggregator` uses the versioned `shadow-rule-v1` policy. Gate failures/errors, required checklet error/abstention, high/critical findings, or two distinct medium evidence families produce `would_hard_verify`; otherwise it records `would_waive`. The policy is deterministic and non-probabilistic.

Hard verification has explicit adapters:

- `CommandHardVerifier` invokes an independently configured executable against a materialized immutable artifact;
- fixture evaluation uses an independent fixture oracle mapping unavailable to checklets;
- `StaticHardVerifier` is test-only.

Timeout, missing output, and infrastructure failures are `outcome_unknown` or `infrastructure_error`, never acceptance.

## Telemetry, replay, and evaluation

`JsonlEventSink` appends an event envelope containing schema/event/run/task/artifact identity, component ID/version, and event type. Events distinguish gate/checklet evidence from hard-verifier evidence. Use `--event-log` with the CLI to persist an event stream.

Evaluation fixtures are labeled after prediction. The checked-in `engineering_fixture_set` is intentionally small and identified as engineering fixtures, not a statistically representative dataset. Reports include per-checklet counts/precision/recall where fixture labels permit, unique catches, Jaccard finding overlap, shadow-waiver coverage, observed counterfactual miss rate, indeterminate cases, cost/latency, hard outcomes, and limitations.

Replay consumes a stored `run_to_record()` JSON object, reconstructs frozen bytes, re-runs deterministic stages, and uses the recorded hard outcome. It rejects digest or checklet-version mismatch rather than calling the run scientifically equivalent.

## Developer commands

Run the test suite:

```powershell
python -m unittest discover -s tests -v
```

List registered checklets:

```powershell
python -m verification_v1 list-checklets
```

Run a task and artifact JSON pair. The hard command is required; `{artifact_path}` may be used inside it.

```powershell
python -m verification_v1 run task.json artifact.json --hard-command '"python" -m pytest {artifact_path}' --event-log .verification/events.jsonl
```

Evaluate the fixture suite and write reports:

```powershell
python -m verification_v1 evaluate evals/verification_v1/engineering_fixture_set.json --report-dir reports/verification_v1
```

Replay a saved run record:

```powershell
python -m verification_v1 replay run-record.json
```

## Interpreting results and V2 evidence

The observed counterfactual shadow miss rate is a measurement on the current fixture sample, not a production safety guarantee. Indeterminate outcomes are excluded from success claims. V2 research requires substantially more independently hard-verified examples, nontrivial waiver coverage, measured unique signal and redundancy, stable provenance, useful checklet quality, economic headroom, and an explicitly justified calibration process. If specialized checklets add little signal, simplify rather than force a learned aggregator.
