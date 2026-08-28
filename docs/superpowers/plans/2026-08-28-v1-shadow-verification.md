# Verification Slice V1 Implementation Plan

> **For agentic workers:** Execute this plan inline with red/green checks at the public runner and CLI seams.

**Goal:** Build a local, content-bound verification experiment where diagnostic coding checklets make an auditable shadow decision while an independent hard verifier always remains authoritative.

**Architecture:** A dependency-free Python package uses immutable artifact records, explicit dataclass contracts, a versioned deterministic policy, JSONL telemetry, and a coding domain pack. The runner owns the sequence and always invokes the hard verifier after gates/checklets; evaluation consumes independent fixture labels only after prediction.

**Tech Stack:** Python 3.14 standard library, `unittest`, JSON/JSONL, `argparse`, `subprocess`.

## Global Constraints

- No third-party dependencies or service framework.
- `would_waive` is counterfactual only and cannot accept an artifact.
- Checklets are read-only, diagnostic-only domain-pack components.
- Every decision result binds the same SHA-256 artifact digest.
- Fixture oracle labels are unavailable to checklets.
- Reports use experimental language and never claim safe/certified waivers.

---

### Task 1: Contracts, immutable artifacts, and telemetry

**Files:**
- Create: `pyproject.toml`, `verification_v1/contracts.py`, `verification_v1/artifacts.py`, `verification_v1/telemetry.py`, `tests/test_artifacts_and_contracts.py`

**Interfaces:** `ArtifactStore.register_bytes(content, artifact_type, run_id, metadata) -> RegisteredArtifact`; all outcome contracts expose `to_dict()`.

- [ ] Write digest stability/mutation and complete-envelope tests; run `python -m unittest tests.test_artifacts_and_contracts -v` and observe import failure.
- [ ] Implement frozen explicit contracts, canonical serialization, filesystem content-addressed registration, and append-only event envelopes.
- [ ] Re-run the focused tests and require exit code 0.

### Task 2: Domain pack, gates, checklets, policy, and hard verifier

**Files:**
- Create: `verification_v1/domain.py`, `verification_v1/gates.py`, `verification_v1/checklets.py`, `verification_v1/aggregation.py`, `verification_v1/hard_verify.py`, `tests/test_checklets_and_policy.py`

**Interfaces:** `CodingDomainPack.default()`, `CheckletRegistry.run_all(context)`, `ShadowAggregator.assess(gates, observations)`, `HardVerifier.verify(artifact, task)`.

- [ ] Add public behavior tests for structured checklet output, abstention/error fail-closed policy, and an executable hard-verifier adapter; observe red tests.
- [ ] Implement five narrow deterministic coding checklets and a versioned transparent policy; add command and fixture hard-verifier adapters with explicit unknown/infrastructure outcomes.
- [ ] Re-run this focused suite and require exit code 0.

### Task 3: Authoritative runner and telemetry sequence

**Files:**
- Create: `verification_v1/runner.py`, `tests/test_runner.py`

**Interfaces:** `VerificationRunner.run(task, artifact, hard_verifier) -> VerificationRun`; `VerificationRun.final_outcome` derives solely from `HardVerifierResult`.

- [ ] Add the structural red tests: clean/checklet-shadow waiver + reject oracle remains rejected, checklet error forces `would_hard_verify`, and unknown is not accepted.
- [ ] Implement the fixed sequence `artifact -> gates -> checklets -> shadow -> hard verifier -> comparison -> events`; reject digest mismatch and provide no early accepted path.
- [ ] Run runner tests, including the independent-oracle adversarial fixture, and require exit code 0.

### Task 4: Evaluation, replay, reports, and CLI

**Files:**
- Create: `verification_v1/evaluation.py`, `verification_v1/cli.py`, `verification_v1/__init__.py`, `verification_v1/__main__.py`, `evals/verification_v1/engineering_fixture_set.json`, `tests/test_evaluation_and_cli.py`

**Interfaces:** `evaluate_fixture_set(path) -> EvaluationReport`, `replay(record) -> VerificationRun`, `python -m verification_v1 {run,replay,evaluate,list-checklets}`.

- [ ] Add red tests for metrics, replay digest preservation, report content, and CLI discovery.
- [ ] Implement six labeled engineering fixtures (four seeded defect families plus clean controls), label-after-prediction evaluation, metric/overlap calculation, report emission, and minimal CLI wiring.
- [ ] Run focused evaluation/CLI tests and require exit code 0.

### Task 5: Documentation and final validation

**Files:**
- Create: `docs/verification/v1-shadow-verification.md`, `README.md`
- Modify: implementation/test paths only as required by failures found in Task 4.

- [ ] Document purpose, non-goals, flow, identity, checklet contract, telemetry, evaluation, replay, metrics, V2 evidence, and developer commands.
- [ ] Run `python -m unittest discover -s tests -v`, `python -m verification_v1 evaluate evals/verification_v1/engineering_fixture_set.json --report-dir reports/verification_v1`, and `python -m verification_v1 list-checklets`.
- [ ] Inspect one clean, seeded defect, false-shadow-waive, checklet-error, and unknown fixture result; confirm reports/events carry the required identity and component versions.

## Definition of Done

The runner never maps a shadow result to acceptance; each runnable fixture invokes the configured hard verifier against the registered artifact digest; the full standard-library suite and fixture evaluation pass; JSON and Markdown reports expose indeterminate counts, per-checklet metrics, overlap, cost/latency, and counterfactual shadow metrics; the documentation explicitly keeps this at VS-V1 experimental scope.
