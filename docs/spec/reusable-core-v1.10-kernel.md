# The Reusable Core — Normative Kernel, v1.10

### A verification-first, risk-bounded, domain-agnostic agent loop

> **Status of this document.** Normative. This kernel is the single source of truth for what the Reusable Core *is*: its separations, estimands, invariants, contracts, transitions, and build order. It is deliberately short. Everything it summarizes is specified in detail in the reference volumes under [`volumes/`](volumes/), which remain normative *detail* beneath it.
>
> **Status of the implementation.** Every normative section ends with an **Implementation status** block measured against `markwuenschel-dev/Reusable-Core` at commit `30aaa7d` (2026-09-21, `main`). Status is a factual claim about the repository, not an aspiration. It must be updated in the same pull request that changes it.
>
> **Supersedes.** Reusable Core v1.9 and its companion documents (implementation profile 1.x, research program v1.9, trusted-runtime / Model Factory v1.9, and the RQ17/RQ18/RQ26 integration revisions). Their content is preserved without loss in the volumes; see [`README.md`](README.md) for the supersession map.

---

## 0. How to read this

### 0.1 Document stack and precedence

```text
KERNEL (this file)                                   normative — wins every conflict
  Vol. I   Core architecture detail (CORE v1.9)       normative detail
  Vol. II  Canonical implementation profile 2026      normative detail for instantiation
  Vol. III Trusted runtime + Model Factory            normative detail for runtime/learning
  Vol. IV  Research program & experimental contract   NON-normative; grants no authority
  Sources  Routing, trusted-runtime, RQ17, RQ18       NON-normative source research
```

Within Vols. I–III the inherited precedence holds: CORE semantics > canonical implementation decisions > composition findings > runtime findings > certification-durability findings > factory findings > routing findings > vendor defaults.

**Kernel-first rule.** If a volume and this kernel disagree, the kernel wins and the disagreement is a defect to be fixed in the volume. A volume section may add detail, never weaken a kernel rule.

**Load boundary.** Runtime code, registries, and conformance tests cite the kernel and Vols. I–III. Vol. IV and the sources hold priors, treatments, field evidence, and open questions; nothing in them is policy until promoted into the kernel through §19's promotion gates.

### 0.2 Normative language

**MUST / MUST NOT** — required for conformance. **SHOULD / SHOULD NOT** — strong default; deviation requires a recorded deployment decision and conformance argument. **MAY** — optional technique.

### 0.3 Implementation-status legend

| Label | Meaning |
|---|---|
| **BUILT** | Exists on `main`, wired into a production entry point, and covered by tests. |
| **PARTIAL** | Some of the section exists; the block names exactly what is missing. |
| **NOT STARTED** | No code on `main`. |
| **NEXT** | Not started, and it is the next build step under §20. At most one milestone is NEXT at a time. |

"Covered by tests" means the repository's own suite. Under §9.5 that is not yet an instantiation proof; a status of BUILT does not claim one.

### 0.4 Where the repository stands (dashboard)

| Kernel area | Status | One-line evidence |
|---|---|---|
| §2 Keystone estimands | PARTIAL | V1.2 analysis computes shadow κ, observed miss rate, Wilson bounds; no `L_escape`/`C_complete` |
| §3 Governed transitions | NOT STARTED | No monitor, ledger, or commit protocol; `final_outcome` comes from the hard verifier only |
| §4 Invariant register | NOT STARTED | No `invariants.yaml`; invariants live as unit tests |
| §5 Policy composition | NOT STARTED | — |
| §6 Loop, producer, B0 baseline | **NEXT** | No producer and no model call exist; candidates arrive pre-built |
| §7 Broker and effects | NOT STARTED | Hard verifier runs candidate code in a materialized subprocess workspace; no broker/grants/slots |
| §8 Verification stack | PARTIAL | L1 metadata gate, L3 `CommandHardVerifier`, 5 diagnostic checklets; no L2/L4/L5/L6, no profiles |
| §9 Verifier authority & instantiation proofs | PARTIAL | Checklets hard-capped at `diagnostic`; typed `abstain`/`error`; no profiles or wiring proofs |
| §10 Aggregation & certification governor | PARTIAL | `shadow-rule-v1.1` + V1.2 evidence program; decision gate returns `COLLECT_MORE_V1_2_DATA` (0/50 real tasks) |
| §11 Certification durability | NOT STARTED | SHA-256 digests are the only *artifact* content identity |
| §12 Compositional assurance | NOT STARTED | — |
| §13 Contracts and handoff | PARTIAL | `TaskContract`, `ArtifactRef`, `coding_bundle/1.0.0`; no producer contract, no `RequirementTrace` |
| §14 Memory | NOT STARTED | — |
| §15 Federation | NOT STARTED | — |
| §16 Telemetry | PARTIAL | Append-only JSONL events with identity envelope; unauthenticated, no closed schema, no `core_lint` |
| §17 Runtime, stopping | PARTIAL | Typed `outcome_unknown`/`infrastructure_error`; no resource governor or stopping controller |
| §18 Learning & Model Factory | NOT STARTED | Correctly deferred (§20 Phase 6) |
| §19 Evaluation & promotion | PARTIAL | Grouped hash partitions, sealed holdout/calibration, fixture evaluation; only rung B3 exists (B0–B2, B4–B7 absent) |
| §20 Build order | — | Repository is a Phase 4 slice built before Phases 0–3 |

---

## 1. Thesis and the six separations

> **Agents are optional implementation strategies. The durable core is artifacts, typed contracts, verification-first decision logic, governed authority over consequential transitions, and total-path telemetry. Specialization is supplied by capability-composed domain packs, never by a permanent agent topology.**

The security target is:

```text
compromised intelligence  ⇏  unauthorized authoritative effect
```

The epistemic target is:

```text
recursive intelligence  ⇏  recursive truth
```

The system MUST preserve six separations. Each is a structural fact about who holds which authority, not a tunable policy.

1. **Competence is not authority.** `ExecutionCapability` says an executor *can* do a class of work. `AuthorityGrant` says a principal *may* do a named action, now, on named resources, under a frozen policy.
2. **Production is not verification.** Producers create candidates. Verifiers emit evidence. Monitors and controllers authorize transitions.
3. **Epistemic authority is not effect authority.** A trustworthy verdict confers no ability to mutate, publish, release, deploy, send, or commit.
4. **Evidence is not truth.** Tests, signatures, traces, model judgments, receipts, and human decisions each carry an applicability and validation boundary.
5. **Optimization is not governance.** Routers, schedulers, and learned policies may propose the cheapest useful next action. They may not mint permission, waive mandatory verification, or release an artifact.
6. **Recursive evidence is not independent evidence.** *(New in v1.10 as a kernel separation; previously in the implementation profile and INV-G12.)* Agreement, repetition, successful reuse, model-family diversity, or recursive descent do not create external grounding. Evidence produced by models, verifiers, routers, synthetic generators, teachers, or descendants of the active portfolio retains its causal provenance.

The target is one control plane that can enter unfamiliar tasks, repositories, and substrates without inheriting undeclared authority or hidden state. It composes only the machinery a run earns, but is complete enough to mediate every consequential path it permits.

**Detail:** Vol. I §0; Vol. II §1.4, CDR-013.

**Implementation status — PARTIAL (2 of 6 embodied).** Separation 2 is enforced inside the verification slice: `VerificationRunner.run()` always invokes the hard verifier, and `VerificationRun.final_outcome` derives only from `HardVerifierResult` (`verification_v1/runner.py`). Separation 4 is embodied in typed outcomes (`outcome_unknown`, `infrastructure_error` never become acceptance). Separations 1, 3, 5, 6 have no mechanism because there are no principals, effects, routers, or learned components yet.

---

## 2. Keystone estimands and the decision hierarchy

### 2.1 Exact end-to-end estimands

Artifact acceptance is **selective prediction with deferral**. For each request:

- `A = 1` when the **exact terminal artifact digest** is accepted;
- `V = 1` when that exact artifact received qualifying independent verification before acceptance;
- `W = A·(1−V)` — accepted through a certified waiver;
- `B_ref = 1` when the frozen reference protocol says it should not have been accepted.

```text
κ       = Pr(W=1)                               waiver coverage
R_fw    = Pr(B_ref=1 | W=1)                     conditional false-waiver rate (undefined at κ=0)
L_fw    = κ·R_fw                                absolute false-waiver load
ν       = Pr(A=1 ∧ V=1)                         verified-acceptance mass
R_v     = Pr(B_ref=1 | A=1 ∧ V=1)               verified-path residual error
L_escape = Pr(B_ref=1 ∧ A=1) = κ·R_fw + ν·R_v   bad-accept load
R_accept = L_escape / Pr(A=1)
C_accept = Pr(A=1)          C_complete = Pr(declared terminal disposition reached)
```

Reports MUST carry `L_escape`, `R_accept`, `κ`, `ν`, `C_accept`, and `C_complete` together; a system cannot claim quality by refusing everything. Verify-all and fail-closed modes are safe fallbacks with `κ = 0`; they are not certified waiver policies and define no `R_fw`. Every bound is labeled with its oracle class; in oracle-poor domains `B_ref` means disagreement with the frozen adjudication protocol, not truth.

### 2.2 Sibling spines

The same selective-decision pattern governs four surfaces whose losses MUST NOT be collapsed into one scalar:

| Spine | Decision | Required reporting | Primary control |
|---|---|---|---|
| Artifact waiver | accept without qualifying verification | `κ, R_fw, L_fw, L_escape, R_accept`, coverage | calibrated evidence + certification governor (§10) |
| Memory promotion | make derived memory production-eligible | `κ_p, R_fp^(a), L_fp`, utility, contamination `R_c` | lifecycle + promotion authority (§14) |
| External effect | realize a consequential state change | unauthorized-effect events/UCBs by severity, reconciliation | mediation + grants + effect slots (§7) |
| Federated release | release across a trust boundary | invariant conjunction, noninferiority margins, disclosure | declared closure + foreign verification (§15) |

A correct artifact obtained through credential exfiltration is an authority failure; a wrong artifact with no unauthorized effect is a quality failure. Neither compensates for the other.

### 2.3 Decision hierarchy — lexicographic over declared budgets

```text
0. Hard structural invariants (§4)
1. Authority feasibility (grants, certificates, always-verify rules, human-only ceilings)
2. Severe-risk chance constraints   U_δ(R_ue,critical) ≤ β_j ; R_c < 1 ; harm strata
3. Certified selective-risk bounds  U_δ(R_fw,g) ≤ α_g ; U_δ(R_fp^(a)) ≤ α_a ; coverage floors
4. Final-quality noninferiority vs. matched baselines (B0 / M1 / X0)
5. Pareto optimization (total path cost, p95 latency, verifier volume, human volume, disclosure)
6. Scalar utility — sensitivity analysis only, never selection
```

A change is promoted only if it improves the holdout frontier under equalized metered budgets **and** keeps every tier above it intact. No cost saving buys back a failed higher tier.

**Detail:** Vol. I §1–§1.2, §6.7; Vol. II §13.2.

**Implementation status — PARTIAL.** `verification_v1/analysis.py` and `v12_report.py` compute shadow waiver coverage (counterfactual κ), observed counterfactual miss rate with Wilson 95% intervals, per-checklet criterion metrics, and lift, with unknown/infrastructure outcomes excluded from the miss-rate and unnecessary-verify denominators (shadow κ is computed over all records, including indeterminate ones). Missing: `ν`, `R_v`, `L_escape`, `R_accept`, `C_complete`, the sibling spines, and any tier-ordered promotion logic. Note that every current κ is counterfactual: no artifact is ever accepted by waiver.

---

## 3. Governed transitions

A **governed transition** is any consequential state change: unverified acceptance, memory promotion, authoritative artifact promotion, external effect, federated release, pack/spine activation, model/router promotion, or protected canon/policy mutation. It MUST occur only through an **Authorization Monitor** that:

1. validates the exact subject digest, effective-policy digest, certification or authority closure, certified context hash, resource scope, and validity epoch;
2. evaluates declared `IndependenceProfile` and `OracleProfile` predicates for the transition;
3. fails closed on unknown provenance, scope, support, compatibility, policy composition, or invalidation state;
4. writes through the authority ledger under its own authenticated principal;
5. proves its invalidation watermark is current against the authoritative head;
6. delegates the commit to the broker or a controller that does not share the producer's mutation authority.

| Transition | Monitor | Instrument |
|---|---|---|
| Accept without qualifying verification | Certification governor | `AuthorityCertificate` bound to `CertificationClosure` and `CCH` |
| Promote runtime memory | Memory promotion authority | outcome + transition attestations |
| Realize an external effect | Runtime tool broker | `AuthorityGrant` + `EffectSlot` + operation record |
| Release across a boundary | Release controller | foreign verification + release-time closure recheck |
| Activate a pack/spine configuration | Release controller | `PackCompositionManifest` + `InteractionCertificate`s (§12) |
| Activate a learned router/model/verifier | Promotion monitor | promotion hierarchy + epistemic-stability gate (§18) |
| Mutate protected canon, policy, permissions, root trust | Authenticated human owner (optional dual control) | signed protected-tier approval — **no automatic path** |

### 3.1 Commit protocol

```text
1. snapshot subject, policy, closure, CCH, lease, invalidation head
2. validate subject + authority preconditions against the snapshot
3. resolve policy composition; reject unresolved contradiction
4. reserve the effect slot or terminal-decision slot
5. mint a one-use grant bound to reservation + snapshot
6. immediately before commit: recheck digest, lease/fence, grant, certificate, watermark
7. execute through the broker-owned adapter or controller
8. obtain an independent effect / receipt / terminal-artifact observation
9. reconcile ambiguous outcomes — never blind-retry a consequential operation
10. append the terminal authority record; publish the decision
```

Each transition type declares one **linearization point**. Validation before it is provisional; an invalidation, lease loss, digest change, or closure change before it aborts or revalidates the transition.

**Common-substrate hardening.** Monitor-specific keys and append-only partitions; independently witnessed ledger checkpoints; durable monotonic invalidation offsets; fail-closed on missing or stale watermark; no inherited identity field is authority; no monitor approves its own ledger write or witnesses its own checkpoint.

**Detail:** Vol. I §1.3; Vol. II §5 (PostgreSQL head, outbox, JetStream, fencing), §6.

**Implementation status — NOT STARTED.** No monitor, ledger, invalidation head, lease, or commit protocol exists. The nearest analogue is that the hard-verifier result is the only path to `final_outcome`, which embodies separation 2 but is not a governed transition.

---

## 4. The invariant register

The authoritative register is `invariants.yaml`, pinned by `registry.manifest.yaml`. Runtime code loads mechanical and architectural rows directly; telemetry violations reference one invariant ID; packs MAY add namespaced invariants and tighten core ones but MUST NOT remove or weaken them. **An invariant referenced in prose but absent from the pinned register is unknown policy and fails closed.**

| Family | Kernel-level content |
|---|---|
| **Global `INV-G*`** | exact-object authority; fail-closed unknowns; non-compensable harms (G3); no inert assurance (G5); no self-attestation, with consumer-observed wiring proofs (G6); instantiation-proof discipline (G6–G8, per RQ15); additive repair forbidden, superseded paths deleted (G8); protected control-plane boundary; monotonic policy composition; typed missingness; witnessed authority freshness; recursive-evidence provenance (G12) |
| **Authority/effects `INV-A*`** | complete mediation; no amplification; terminal non-elevatable mechanical failures; principal separation; effect cardinality `N_commit ≤ m` (A5); credential isolation; evidence-write authority (A7); isolated compute; atomic governed commits |
| **Memory `INV-M*`** | evidence-first birth; eligibility-before-ranking; protected-canon firewall; provenance-family support counting (M4); descendant revocation |
| **Certification `INV-C*`** | exact closure-bound and CCH-bound certificates; mutation invalidation (C2); `R_fw` undefined at zero coverage; path-specific causal certification; never self-renewing |
| **Composition `INV-P*`** *(new family in v1.10)* | no modular credit without contract, state, authority, evidence, global-property, and usage-domain closure; evidence never multiplies across shared provenance |
| **Federation `INV-F*`** | artifact integrity; declared closure; at-most-one logical effect; no stale release; verifier isolation (F5); disclosure containment (F1–F6) |

Enforcement modes: **architectural** (the forbidden path does not exist), **mechanical** (deterministic rejection), **statistical** (permanent audit bounds the residual rate), **procedural** (authenticated human or dual control).

The full numbered register is authored in `registry/invariants.yaml` (§20, Phase 0); the kernel names families and the IDs already cited across the corpus. New IDs are assigned only in the register.

**Detail:** Vol. I §1.4, §13 (registry package); Vol. II §19 (invariant-to-mechanism map).

**Implementation status — NOT STARTED.** No `invariants.yaml`, `codes.yaml`, `state_machines.yaml`, `registry.manifest.yaml`, or `core_lint.py` exists. Several invariants are enforced *ad hoc* and tested (`tests/test_safety_invariants.py`, `tests/test_v12_safety_invariants.py`): checklet authority ceiling is `diagnostic` (`CheckletSpec.__post_init__`), unknown outcomes never accept, artifact digests bind every record. Those tests are the seed of the register.

---

## 5. Effective-policy composition

Every applicable core, deployment, pack, tenant, task, and incident policy normalizes into one `EffectivePolicy` through `policy_composition.yaml`:

| Dimension | Composition |
|---|---|
| permissions, resources, effects, disclosure allowances, network destinations | intersection |
| explicit denials, required gates, always-verify rules, human-review triggers | union |
| authority ceiling, risk tolerance, validity interval, budget ceiling | most restrictive |
| sandbox requirements | strongest jointly realizable profile |
| canonicalization and schema requirements | exact compatibility or declared adapter proof |
| unresolved contradiction | terminal `policy_conflict` |

Every composition emits `parent_policy_digests[]`, the normalized policy, `effective_policy_digest`, `non_expansion_proof`, and `conflicts[]`. A generated or learned policy is eligible only with a non-expansion proof against every parent. Order-dependent combining MUST either be eliminated or have its order fixed and certified (§12).

**Canonical engines (Vol. II CDR-002):** Cedar inside a Core-owned authorizer is the semantic authority; OPA is platform policy and may narrow but never expand Core authority.

**Detail:** Vol. I §1.5; Vol. II §4.

**Implementation status — NOT STARTED.**

---
## 6. The loop, the producer, and the B0 baseline

### 6.1 Component model

| Component | Job | Authority |
|---|---|---|
| Orchestrator / router | choose path, pack, budget; invoke roles and checklets; stop or escalate | policy-authoritative; never authors artifacts |
| Producer(s) — planner, architect, researcher, **builder**, documentor | decide, synthesize, generate | generate only |
| Constraint extractor | request + context → machine-checkable requirements | read-only |
| Verification stack | narrow checklets → calibrated aggregator (the "critic" dissolves here) | diagnostic by default |
| Hard verifier(s) | high-fidelity adjudication (CI, execution, claim audit, human read) | authoritative within its oracle boundary |
| Adversarial prober | generate an input that breaks the artifact | evidence; a confirmed executable break is objective |
| Integration authority | the one writer of the canonical candidate per scope and revision | one per artifact scope and revision transaction |
| Runtime tool broker | sole path for external effects | trusted computing base |
| Authorization monitors | governor, memory authority, broker policy, release controller, promotion monitor | distinct principals; never a producer |
| Resource governor | tokens, latency, cost; reserves assurance budget first | spending only; no waiver authority |
| Telemetry learner | learn routing, risk, calibration, stopping | advisory until promoted (§18) |

Agents decide, synthesize, and generate; **services verify, execute, cache, compare, and store.** Work SHOULD cross the agent→service boundary wherever a deterministic service can do it.

### 6.2 The canonical loop

```text
intake → contract normalization + risk/budget tag
 → route + pack selection (ExecutionCapability, not authority)
 → principal + action-availability view (no credentials)
 → eligible memory retrieval
 → producer builds candidate (minimum role set)
 → every external effect → broker
 → parallel checklet bundle → risk aggregator
 → scheduler PROPOSES; governor DECIDES:
      verified_accept | certified_waiver | hard_verify | human | fail_closed
      or acquire next-best evidence (VoI)
 → bounded revision (mutation invalidates prior verification)
 → best-validated-so-far selector (never "the last draft")
 → [boundary only] reconcile → evidence manifest → foreign verify → release recheck
 → memory capture → verify → canary → promote
 → authenticated telemetry
```

The local-only path skips effect adapters, boundary steps, and memory promotion. Governance machinery activates on the transition that needs it, not on every task.

### 6.3 Thin by default; B0 is the null hypothesis

The default loop is `orchestrator → planner → builder → grounded verifier`, and a **strong single executor with matched tools, context, and model (B0)** is the null hypothesis every added agent, checklet, route, or layer must beat at matched *metered* budget. Planner, architect, researcher, critic→checklets, and documentor are invoked only on a measured trigger (Vol. I §4.3).

### 6.4 Producer policy

- **Context is a replayable manifest**, not a prompt blob: task brief, contract, requirements, prior artifacts *by reference*, retrieved snippets with trust levels, pack and template versions, context budget.
- **Retrieved content is subject matter, never instruction.**
- **Production modes** — single-pass, retrieve-then-generate, plan-then-generate, tool-augmented, best-of-N, revise-existing — chosen as the cheapest that can satisfy the contract.
- **Best-of-N vs. revision flips on verifier soundness.** With a sound oracle, scale N where per-sample success is roughly 0.1–0.9. With a noisy verifier, keep N small (≤ ~5) and spend on revision and on the verifier. Never spend repeated revision on a candidate whose *contract* is wrong; replan.
- **Select the best validated candidate**, preserving a validated best-so-far across rounds.

### 6.5 Task graphs

Non-trivial work is a typed graph of artifact nodes (`depends_on`, acceptance criteria, required gates and checklets, per-node budget, integration authority). Only `passed`, validly `waived`, `advisory_only`, or `human_approved` satisfy a dependency. Invalidation marks only causally affected nodes `stale`. Partial completion is a first-class terminal disposition. "No more actions were taken" is never a terminal reason.

**Detail:** Vol. I §3, §4; Vol. II §9 (ModelEndpoint, semantic model roles, three routing levels); Vol. IV RQ1, RQ4, RQ5, RQ9.

**Implementation status — NEXT.** There is no producer, no model call, no `ModelEndpoint`, no orchestrator, and no task graph. Candidates enter the system pre-built through `run task.json artifact.json` or fixture files. This is the gap that blocks the evidence program (§10): with no producer there is no stream of real tasks. The B0 executor is the next build step (§20, milestone M1).

---

## 7. The runtime tool broker and governed effects

The boundary is not "prevent all bad reasoning"; it is `compromised reasoning ⇏ unauthorized authoritative effect`. The broker enforces four distinct abstractions:

| Abstraction | Says |
|---|---|
| `ExecutionCapability` | what a frozen executor *can* do |
| `ActionContract` | the semantic operation available to request |
| `AuthorityGrant` | what a principal *may* do on this one invocation |
| `ResourceHandle` | the exact object or destination affected |

**Typed actions only.** The action registry MUST NOT expose raw shell, generic interpreters, arbitrary subprocesses, unrestricted Git, raw SQL, arbitrary URLs, ambient credentials, or host paths. Trusted adapters may use those internally; the requester sees only the semantic action. `run_task(command)` re-creates ambient authority and is forbidden.

**Isolated compute cells.** Arbitrary code runs only inside a cell: ephemeral or branch-local filesystem; no ambient credentials; network denied by default with named mediated reads; no authoritative shared writes; mandatory resource limits; content-addressed declared inputs; outputs leave only through validated export. A platform that cannot realize the declared isolation profile marks the action **unavailable**; it never silently downgrades.

**Grants.** Out-of-band, one-use, bound to issuer, audience, principal, run, action ID and implementation digest, resource handles, parameter digest or envelope, sandbox and network profile, effective-policy digest, validity window, max uses, effect slot, operation ID, and invalidation watermark. High-risk effects are broker-owned; agents never hold the committing credential.

**Effect slots.** One slot per semantic intent with maximum commit cardinality `m`. Same operation + same parameter digest joins; same operation + different digest is an idempotency conflict; a new operation ID is not a new intent. `N_commit ≤ m` always. Ambiguous provider outcomes become `outcome_unknown` and are reconciled against receipts and independent observation; consequential operations are never blind-retried. A high-impact action whose provider supports neither idempotency nor reconciliation is not an eligible autonomous action.

**Mechanical errors are terminal and non-elevatable.** Parser failures, unknown actions, scope violations, forbidden resources, network violations, policy and idempotency conflicts create no effect and no approval prompt. `broker = denied ∧ state = changed` is a containment bypass.

**Principals.** Producer, verifier, integration controller, certification governor, and release controller are distinct principals with distinct credentials, action subsets, writable mounts, networks, and audit identities.

**Detail:** Vol. I §4A; Vol. II §4.1 (SPIFFE), §6 (broker), §7 (sandbox tiers); Vol. IV RQ12 (`AUTH-T1…T5`).

**Implementation status — NOT STARTED, with one relevant precursor.** `CommandHardVerifier` (`verification_v1/hard_verify.py`) materializes the patched repository in a fresh workspace, injects independent reference tests, runs a configured command with a timeout and process-tree kill, rechecks the artifact digest afterward. INTEG-026 blocks candidate control of the judging interpreter; INTEG-007/027/029/031 make materialization failure an `infrastructure_error`, kill the whole process tree on timeout, digest the workspace surface, and handle exit code 5. That is the seed of an isolated compute cell, but it declares no sandbox profile, does not deny network, and **passes the parent's full environment to the candidate command** (`env = os.environ.copy()`), so there is no credential isolation. It holds no effect authority only because nothing in the system has any. There are no principals, grants, action registry, or effect slots.

---

## 8. The verification stack

Use the cheapest, strongest, least-gameable signal available for each quality dimension. **An LLM judge never overrules a failed objective gate.**

| Layer | Gates | Semantics |
|---|---|---|
| L0 Task/contract | type, constraints, budget, risk, pack | ambiguous or high-impact → clarify or triage before any agent runs |
| L1 Deterministic | schema, required fields, formats, dependency refs, prohibited patterns | fail-closed total function |
| L2 Static | lint, types, cycles, security scans, graph checks | high-confidence high-severity blocks; rest informs |
| L3 Execution | compile, tests, property/fuzz, replay, smoke | strongest behavioral signal where an oracle exists |
| L4 Source/claim | resolution, span match, support, freshness | claim-level, not "sounds factual" |
| L5 Residual judging | only the subjective residual | calibrated judges; never overrules L1–L4 |
| L6 Human | high-impact, ambiguous, disagreement, calibration and holdout labels | where it matters most |

Rules that travel with the stack:

- **Push the deterministic boundary.** Decompose rubrics into checkable sub-criteria; anything expressible as a total function artifact→{pass, fail} is deterministic-eligible.
- **Judge mode by job.** Pointwise rubric for in-loop gating; pairwise against mediocre anchors (Bradley-Terry) for selection. Never mix modes within a dimension.
- **Judge hardening.** Both orders; length control; multi-family panels, never the generator's family; pinned `(judge_id, rubric_version, prompt_hash)`; κ ≥ 0.6 against humans before any promotion use.
- **Adversarial generation is a second mode**, run in parallel and risk-triggered. A confirmed executable break outranks any judge; a claimed break is refuted by default.
- **Evidence ladder.** `claim-only → located → triggered → executable`. Block authority requires at least a falsifiable trigger; waivers require affirmative evidence of cleanliness, never absence of checking.
- **One gate-runner.** Hash-pinned ruleset, tiered early exit, one event per check, standard exit codes.

**Detail:** Vol. I §5–§5.6.

**Implementation status — PARTIAL.**
- **L1:** `MetadataShapeGate` via `GateRunner` (`verification_v1/gates.py`). Not a pinned ruleset; no gate-runner CLI per §8.
- **L3:** `CommandHardVerifier` with independent reference files the checklets never see. **BUILT.**
- **Checklets:** five deterministic coding checklets (requirement coverage, test adequacy, change scope, dependency/integration risk, error/boundary) in terminable isolated processes with typed errors (`verification_v1/checklets.py`). **BUILT** as shadow-only diagnostics.
- **Findings:** `CheckletObservation` carries `locus` and `trigger_refs`; there is no evidence-level field, so the evidence ladder is not represented.
- **Missing:** L0, L2, L4, L5, L6, adversarial prober, judge machinery.

---

## 9. Verifier authority and instantiation proofs

### 9.1 Four gates

A verifier earns authority through: **schema** (malformed → `mechanically_invalid`/`abstain`), **evidence** (findings carry the evidence their authority level requires), **oracle** (applicable and validated for the property), and **calibration** (residual judgment meets the slice- and severity-specific threshold).

### 9.2 Profiles, not ranks

`IndependenceProfile` records principal, model-family, prompt-lineage, prior-conclusion, evidence-family, toolchain, execution-environment, and organizational separation. `OracleProfile` records oracle class, repeatability, specification soundness, implementation conformance, applicability, known false-accept and false-reject rates, and validated slices. Transitions evaluate explicit predicates over profiles. No automated principal may self-declare stronger independence. A deterministic check is repeatable, not infallible.

### 9.3 Rollout

Every verifier moves `shadow → advisory → scoped_auto_block`, per validated slice, with automatic demotion on drift, invalid wiring, unsupported oracle status, or precision loss. The domain's strongest oracle sets the ceiling.

### 9.4 Typed incompleteness

Every planned checklet yields a `CheckletObservation` with `requiredness ∈ {mandatory, conditional, optional}` and `state ∈ {not_selected, not_applicable, running, clear, finding, abstain, mechanically_invalid, outcome_unknown, cancelled}`. None but `clear` is affirmative evidence of cleanliness. A mandatory or triggered checklet ending incomplete blocks its scope. Confirmed findings survive unrelated lane failures.

### 9.5 Instantiation proofs

A component is not implemented because its code exists or its own tests pass. Load-bearing instantiation requires:

1. **Consumer-observed wiring proof** — a test drives the production entry point and an independent consumer observes the effect. A writer asserting on what it just wrote is zero evidence.
2. **External-boundary contract proof** — every external wire has a scheduled non-hermetic check, or it is declared unverified and nothing load-bearing rests on it.
3. **Evidence-family accounting** — record count never substitutes for independence.
4. **Typed incomplete outcomes** (§9.4).

### 9.6 Why this section exists

These rules are field evidence, not theory. The E1 deployment (`ibkr-auto-trader`, July 2026; Vol. IV §E1) failed through self-attestation, inert assurance, interpreter escape, dropped findings, identity bleed, unauthenticated telemetry, untouched wires, and additive repair, while showing 1,041 passing tests. **Passing tests are not an instantiation proof.**

**Detail:** Vol. I §5.7–§5.8; Vol. IV §E1, RQ15.

**Implementation status — PARTIAL.**
- Checklet authority is hard-capped at `diagnostic` (`CheckletSpec.__post_init__` raises otherwise). **BUILT.**
- Checklets receive a disposable metadata copy and never see the hard-verifier outcome, fixture label, or another checklet's result. **BUILT.**
- Typed incompleteness exists in reduced form: `CheckletVerdict ∈ {clean, finding, abstain, error}`, with timeout, missing context, exception, and malformed output all mapped to typed `error`. The kernel's nine-state set and `requiredness` are not yet represented. **PARTIAL.**
- `IndependenceProfile`, `OracleProfile`, and the rollout state machine are **NOT STARTED**. Each observation has an `evidence_family_id` field, but nothing accounts across it.
- **No consumer-observed wiring proof or non-hermetic boundary check exists.** The only external wire is the hard-verifier subprocess, and it is exercised by the repository's own tests.

---

## 10. Risk aggregation and the certification governor

### 10.1 Calibration to guarantee

If the aggregator emits calibrated `s` and the policy waives when `s ≤ τ`, then `R_fw(τ) ≤ τ + ε_cal`. **Tail calibration near the threshold matters more than global ECE.** A low score that rests on absence of checking is an unexamined case, not a waiver; it routes to evidence acquisition.

**The oracle defining the loss must be sound**, or the guarantee is vacuous. Similarity-based proxies are not sound oracles.

### 10.2 The aggregator fuses evidence; it does not average scores

Recipe: flexible discriminative aggregator → calibration → finite-sample waive controller, with Dawid–Skene/GLAD to expose drifted checklets. **Redundant checklets exaggerate apparent gain; correlation collapses it.** **Decomposition without calibration is worse than one broad critic:** N checks at a 5% spurious-block rate give `1 − 0.95ᴺ` false-block probability (≈ 54% at N = 15). Tune the suite jointly (Learn-then-Test, FWER) on a held-out split; calibrate per class where classes matter.

### 10.3 Value of information

Default: myopic EVI with a conservative threshold; acquire `argmax VoI_j / c_j`; waive iff `u(s) ≤ α` *and* the bound rests on checks that cleared. A cheap-first cascade pays only if `1 − f_L > c_L / c_H`.

### 10.4 Finite-sample certification

Three layers: conformal risk control / RCPS; Learn-then-Test / Pareto testing for simultaneous constraints; and a **permanent uniform random audit** (rule of three: ~59 / 149 / 299 / 598 audited waivers for 5% / 2% / 1% / 0.5% at 95% with zero misses). Keep a separate targeted stream for learning only. Report one-sided upper bounds, never point estimates; set internal α below the promised bound; halt auto-waiver as the rolling audit approaches α.

**The guarantee changes type with the oracle.** With a sound oracle `R_fw` is a correctness bound. Without one it is an *agreement* bound with a noisy human proxy. They MUST NOT be reported as the same number. Certifying ≤ 2% needs on the order of 150–400 labeled high-severity items per domain per tier; **the labeling budget is the program's critical path.**

### 10.5 The certification governor

A scheduler may *propose* `stop_accept`; only the governor authorizes unverified acceptance. A certificate binds to a **`CertificationClosure`** — the mechanically derived causal slice able to affect the waiver decision for its stratum (reachable scheduler branches, producers, checklets/probers, qualifying verifiers, prompts/tools/schemas, mutation-capable repair paths, terminal policy, parent policy digests, effective-policy digest, closure digest, completeness proof) — and to an exact `CCH` (§11).

The governor checks exact digest, current policy and closure, stratum support, required observation states, qualifying verification, certificate validity and watermark, shift, incident, lease, and always-verify status, absence of post-verification mutation, and coverage floors. It returns exactly one of:

```text
authorize_verified_accept | authorize_certified_waiver
override_to_hard_verify   | override_to_human | override_to_fail_closed
```

A certificate is not a bag of actions; recombining pieces of certified closures yields an uncertified policy. Draft A never authorizes draft B without a validated semantics-preserving transformation. Underpowered high-risk strata remain always-verify.

**Detail:** Vol. I §6; Vol. IV RQ2, RQ3, RQ13 (`SCHED-T1…T6`).

**Implementation status — PARTIAL. This is where the repository has concentrated.**
- `ShadowAggregator` with deterministic `shadow-rule-v1.1`: any gate fail/error, any required checklet error or abstain, and any medium-or-higher finding, or zero observations (INTEG-018) → `would_hard_verify`; otherwise — including low/info findings — `would_waive` (`verification_v1/aggregation.py`). This is baseline rung **B3** (static bundle, no risk model). `would_waive` is counterfactual only and never accepts. **BUILT.**
- The **VS-V1.2 evidence program** is **BUILT**: frozen, reconstructable V1.1 baseline (`validate-baseline`); grouped SHA-256 partitions — 40% development, 20% policy selection, 20% sealed calibration, 20% sealed holdout with one-way `finalize-holdout`; separate criterion-truth and hard-outcome-truth layers; an AST-based independent adjudicator; a fail-closed dataset validator; and a five-way V2 decision gate (`verification_v1/analysis.py`, `evidence.py`, `splits.py`, `independent_adjudication.py`, `v12_report.py`).
- **Current verdict: `COLLECT_MORE_V1_2_DATA`.** 0 of 50 required real determinate tasks; diversity gate failed; all 8 records are controlled fixtures (`reports/verification_v1/v12_latest.md`, generated at `3770d56`, before the PR #6 integrity fixes; regenerate before relying on its exact figures). `evals/verification_v1/real_tasks/` holds only its README.
- **NOT STARTED:** calibrated aggregator, VoI acquisition, conformal or LTT controller, audit streams, `CertificationClosure`, governor, certificates.

---
## 11. Certification durability under drift and change

*(Integrated from RQ18 into the kernel in v1.10.)*

### 11.1 Identity, applicability, and behavior are different objects

Every authority-bearing certificate MUST bind to an exact **Certified Context Hash (`CCH`)**, a Merkle-style digest over the assurance-relevant dependency closure. When relevant to the claim, that closure includes: resolved model/provider identity or digest; prompt and template digests; tool implementation and interface digests; schema and data-contract versions; effective policy, harm hierarchy, and authorization configuration; reference and evaluation protocol, including any judge model and prompt; canonicalization and runtime profile; dependent certificates' CCHs; and the declared operating envelope.

```text
live_cch ≠ certificate.cch   ⇒   the old certificate MUST NOT authorize the live context
```

This is exact for **configuration identity**. It does not claim every byte change alters behavior. The kernel separates:

```text
certificate-instance validity  ≠  evidence applicability  ≠  semantic/behavioral equivalence
```

A context change makes the old certificate non-authorizing. Evidence outside the affected closure MAY carry into a **successor certificate** when its assumptions, reference protocol, freshness contract, and evidence-family applicability still hold.

### 11.2 Certificate states

`VALID · RESTRICTED · SUSPENDED · REVOKED · SUPERSEDED`. `SUPERSEDED` is a valid historical statement about its exact prior context with no authority over the successor. Restriction or suspension can only narrow authority; the authority resolver computes only permissions whose prerequisite claims remain valid.

### 11.3 Three change regimes

```text
observable deterministic change   → exact CCH invalidation
observable stochastic drift       → validated continual monitor (anytime-valid; explicit false-alarm guarantee)
unobservable residual state       → risk-based TTL backstop; fail closed
```

TTL MUST NOT preserve a known-stale certificate. For behavioral fingerprints, the CCH binds the probe specification and baseline, not raw outputs. API-served models whose served version cannot be verified are **provisional by construction**; unverifiable dependency state fails closed.

### 11.4 Differential recertification

The impact object is **`CertificationClosurePlus = DependencyClosure + InteractionClosure`**. Re-run only the claims and interactions a change can affect; reuse applicable evidence; fall back to full recertification when the closure, interactions, applicability, or hidden drift cannot be resolved. Cascade the cost: cheap screen → scoped differential recertification → full recertification. Certificates are **never self-renewing**: renewal is a fresh verification act producing a new certificate.

**Detail:** Vol. II §5.8, §10.4–§10.9, §13.4, §18.7–§18.10, CDR-014–016; Vol. III "Certification durability"; Sources: RQ18 report; Vol. IV RQ18 (`CERT-D*`).

**Implementation status — NOT STARTED.** The repository's only content identity is SHA-256 over canonicalized artifact bytes (`verification_v1/artifacts.py`). That is the right primitive for one leaf of a CCH. There is no context hash, no certificate, and no drift monitor. Two baseline mechanisms are precursors of exact-context identity for the verifier itself (`verification_v1/baseline.py`): the live tree is checked against the `vs-v1.2-runtime-001` runtime baseline, and the frozen V1.1 control is validated from its content-addressed source snapshot alone, never against live code.

---

## 12. Compositional assurance across spines and domain packs

*(Integrated from RQ17 into the kernel in v1.10.)*

**Independent certification is not a composition theorem.** Property composition, evidence composition, and certificate/argument composition are distinct; passing one does not pass the others.

### 12.1 Modular credit requires closure on six channels

A configuration of Core spines and domain packs receives modular reuse only after closure on: **contract** (every assumption discharged; acyclic, or cycles with a well-founded discharge), **state** (disjoint footprints, or certified frame, ownership, serialization, or stability proof), **authority** (no union crossing a harm tier; no ambient shared tool authority; restricted or conservative analysis where exact leakage is undecidable), **evidence** (shared verifier, corpus, simulator, or base model is represented and never multiplied as independent), **global properties** (hyperproperty and probabilistic claims need an applicable composition theorem or a joint argument), and **usage domain** (the configuration stays inside every component's assumption-of-use envelope).

### 12.2 The trigger predicate and the scope ladder

Any unresolved channel creates an interaction hyperedge (Vol. II §10.11 lists all eleven triggers). Each unresolved hyperedge is assigned the smallest defensible scope:

| Level | Scope | Evidence |
|---|---|---|
| `COMP-L0` | all interaction obligations already discharged | compatibility/configuration validation only |
| `COMP-L1` | bounded local interaction | pairwise or small-scope interaction certificate |
| `COMP-L2` | configuration-level interaction | integration certificate over the declared configuration |
| `COMP-L3` | nonlocal, end-to-end interaction | joint recertification |

`COMP-L0` does not waive an externally mandated integration-acceptance process. Pack and spine activation is a governed transition (§3) that fails closed on a missing manifest, an unresolved assumption, unknown shared-state or authority closure, unrepresented evidence dependence, unsupported hyperproperty composition, usage-domain escape, or a wrong-context interaction certificate.

### 12.3 Buy composability by construction

Partitioned state, object-capability attenuation with no ambient authority, append-only content-addressed facts, a single serializing authorization monitor, deny-by-default order-independent policy combination, and provenance tags on every certificate keep most pairs at `COMP-L0/L1`.

**Detail:** Vol. II §10.10–§10.11, §13.8, §18.11–§18.12, CDR-017; Sources: RQ17 report; Vol. IV RQ17.

**Implementation status — NOT STARTED.** There is exactly one domain pack (`CodingDomainPack`, `verification_v1/domain.py`) and no composition, so nothing to compose yet. This is correctly late (§20, Phase 4).

---

## 13. Contracts, artifacts, and handoff

- **Analyze by artifacts, not agents.** Task brief, route decision, plan and acceptance spec, structure spec, evidence pack, candidate, verdict packet, revision diff, release package.
- **Typed contracts.** Every node validates its output against a schema before handoff. The producer contract *requests* actions and authority and never carries credentials. Checklet and prober contracts declare `non_authority: cannot_mutate_candidate`.
- **Schemas without validation are worse than prose.** Pair every schema with evidence-bearing required fields, cross-field checks, and an explicit `abstain`.
- **Requirement traceability is a graph.** `RequirementTrace` states are `preserved | refined | deferred | waived | contradicted | missing | unverifiable`; any missing, contradicted, or unauthorized transformation of a non-waivable requirement is a hard failure regardless of aggregate score.
- **Cross-system handoff** uses a verifier-sufficient manifest: content-addressed artifact, intent and acceptance criteria, consumed facts (assumptions) and established facts (guarantees) addressed by *canonicalized* hash, exit state, invariants, and provenance. A signature makes a claim refutable, never true. Foreign-verifier rejections are attributable to a named field.

**Detail:** Vol. I §7.1–§7.5; Vol. IV RQ6.

**Implementation status — PARTIAL.**
- `TaskContract` holds `task_id`, `requirements`, description, version, and metadata (`verification_v1/contracts.py`).
- `ArtifactRef` and digest-bound records are **BUILT**.
- `coding_bundle/1.0.0` (`base_files` + `overlay`) lets checklets and the hard verifier reconstruct the exact patched repository. **BUILT.**
- **NOT STARTED:** the generic producer contract, `RequirementTrace`, the evidence-level field on findings, and the cross-system manifest.

---

## 14. Governed memory

Memory creation and memory authority are separate. Lifecycle: `evidence → candidate → verified_candidate → canary → promoted`, with `needs_revalidation · quarantined · superseded · revoked · expired`. Only `canary` and `promoted` are retrieval-eligible. Authority classes: `evidence · advisory · operational · protected`. **Protected canon, policy, permissions, and root trust have no automatic runtime write path.** Promotion needs an `OutcomeAttestation` and a `MemoryTransitionAttestation`. Retrieval applies eligibility before ranking; similarity reorders eligible records and never restores an ineligible one. Support counts by provenance family. Revocation traverses descendants. `R_c < 1` is a promotion gate. Learned memory management is shadow-only.

**Detail:** Vol. I §7.6, §6.7; Vol. IV RQ11 (`MEM-M0…M4 × D0…D3`).

**Implementation status — NOT STARTED.**

---

## 15. Federated execution

The unit that crosses a boundary is a **declared execution closure**: an immutable `ExecutionContract`, isolated execution, durable effect state, an `ExecutionEvidenceManifest`, an independent `ForeignVerificationDecision`, and a `ReleaseDecision` after release-time closure revalidation. Six non-compensable invariants apply: artifact integrity, declared closure, at-most-one authoritative logical effect, no stale release, verifier isolation, and no unauthorized disclosure (INV-F1…F6). The guarantee is at-most-one commit per stable logical-effect identity or explicit `reconciliation_required`, never exactly-once. A run or governed scope has **one authority home and epoch**.

**Detail:** Vol. I §7.7; Vol. II §16.5, CDR-005; Vol. IV RQ14 (`FED-X0…X4`).

**Implementation status — NOT STARTED.**

---

## 16. Telemetry and evidence ingress

Authenticated JSONL events validate against a closed `schemas/telemetry_event.schema.json` before append; unknown top-level fields are rejected; domain fields live under `extensions`. The envelope carries schema/event identity, trace links, run and artifact identity, an authenticated **producer principal**, decision, metrics, authority bindings (monitor, policy and closure digests, watermark, grant, certificate, governor decision, slot, operation, ledger checkpoint), and verification profiles. `core_lint.py` enforces registry and cross-field semantics, for example: an unauthenticated producer cannot append production evidence, mechanical invalidity cannot create an approval, and `outcome_unknown` cannot terminate as accepted.

**Generic observability (OpenTelemetry) is diagnostic, never qualifying evidence.** Evidence that can affect authority enters through a separate authenticated evidence-ingress path. Dashboards consume the governed stream; they do not decide health.

**Detail:** Vol. I §8; Vol. II §8.3–§8.4, CDR-012.

**Implementation status — PARTIAL.**
- `JsonlEventSink` appends events with an identity envelope (`schema_version`, `event_id`, timestamp, run/task/artifact identity and digest, `event_type`, component ID and version). Payloads cannot overwrite identity fields. Sink failures are captured as typed `telemetry_failures` that cannot alter the hard outcome (`verification_v1/telemetry.py`, `runner.py`). **BUILT.**
- **NOT STARTED:** a closed JSON schema, the producer principal and authentication, authority bindings, `core_lint`, and separate evidence ingress. Today any process able to write the file can append events. That is E1's "telemetry without producer authority" mechanism, contained here only because nothing consumes these events for authority.

---

## 17. Runtime, faults, and stopping

- Validate structure and evidence semantics before downstream use.
- Retry only idempotent or reconciled operations.
- Persist accepted state after every node; resume from the last valid artifact and current policy snapshot.
- **Never convert an unknown outcome into zero findings or success.**
- The **resource governor** reserves verification and recovery budget before candidate expansion and has no waiver authority.
- Run and lease identity are governed state: atomic snapshots, `run_uid` reconciled with the lease holder, liveness is not identity, distinct closed terminal reasons.

**Stopping.** Self-refinement does not improve monotonically. Stop on plateau (two consecutive rounds below δ), budget, regression versus best-so-far, reward-hacking divergence, or diversity collapse. Always select the best *validated* iteration. `quarantine` and `reconciliation_required` are legitimate non-failure terminal states.

**Detail:** Vol. I §8A, §9.

**Implementation status — PARTIAL.**
- Hard-verifier timeouts, missing output, and infrastructure failures become `outcome_unknown` or `infrastructure_error`, never acceptance. **BUILT.**
- Checklet isolation cleanup kills leftover children so a timeout cannot hang the parent. **BUILT.**
- **NOT STARTED:** resource governor, leases, stopping controller, best-so-far selector. None is needed until a producer exists.

---

## 18. Learning, the Model Factory, and epistemic stability

*(RQ26 integrated into the kernel in v1.10.)*

### 18.1 Four rules for every learned policy

1. It **proposes**; an authorization monitor authorizes.
2. It runs in **shadow** until it beats a transparent baseline on held-out task families.
3. Any policy it generates carries a valid **non-expansion proof** (§5).
4. Drift, missing identity, unsupported scope, or stale closure forces the fixed fallback.

Learned components MAY recommend routing, evidence acquisition, memory promotion, closure checks, or reconciliation effort. They MUST NOT issue grants, certificates, promotions, releases, protected-policy changes, or stronger independence claims.

### 18.2 The factory is self-improving, never self-authorizing

Trace → curation → labeling → dataset → training → evaluation → shadow → candidate report may be automated. **Activation is a governed transition.** Every training example and checkpoint carries complete lineage (data rights, privacy eligibility, label provenance, split locks).

### 18.3 Epistemic stability

Authority stability is not epistemic stability: the microkernel can be perfectly correct while the portfolio becomes self-consistent around a correlated mistake. Therefore:

- evidence keeps **root lineage**, and descendant agreement is never upgraded to independent grounding;
- every adaptive generation keeps a **fresh externally grounded evaluation channel** (uniform audit, with explicit training-exclusion roles);
- comparative routing claims require **logging-policy support** (propensities or paired shadow evidence);
- a recursively trained component increases exposure only after the ordinary promotion hierarchy **and** the epistemic-stability gate pass, with audit cadence able to detect regression before the next adaptation;
- the fallback ladder runs `adaptive recursion → fixed externally anchored recursion → bounded retraining → external-anchor-only retraining → factory shadow-only → frozen portfolio`.

No minimum human-data percentage is canonical; the stability boundary is system- and slice-specific (Vol. IV RQ26).

**Detail:** Vol. I §11; Vol. II §11–§13, CDR-008, CDR-013; Vol. III (Model Factory, router/specialist/verifier factories); Vol. IV RQ26 (`EPI-S*`).

**Implementation status — NOT STARTED, correctly.** Learning is Phase 6 (§20). Two existing pieces are relevant precursors:
- The V1.2 sealed calibration and holdout partitions model the data-role separation this section requires.
- `independent_adjudication.py` does not call the checklet primitives; it reimplements criterion checks on an AST. Lineage is not fully separated, though: it imports criterion definitions from `adjudication.py`, which imports the shared checklet primitives. A small, real, and still imperfect instance of keeping evidence lineage independent.

---

## 19. Evaluation and promotion

### 19.1 Baseline ladder

| Rung | Treatment |
|---|---|
| **B0** | strong single executor, matched tools, context, and model |
| B1 | fixed full loop |
| B2 | reduced default loop (orchestrator + builder + verifier) |
| B3 | static checklet bundle, no risk model |
| B4 | routed loop + rule-based aggregator |
| B5 | routed loop + calibrated risk model |
| B6 | verify-everything ceiling |
| B7 | human/expert reference |

**B0 is the bar most changes must beat.** Equalize budgets by *metered* tokens and tool calls, never nominal caps. Report cost and quality jointly. Treatment labels are namespaced (`BASE-B*`, `FAB-F*`, `MEM-M*×D*`, `AUTH-T*`, `SCHED-T*`, `FED-X*`, `COMP-L*`, `CERT-D*`, `EPI-S*`); a bare `T3` is a schema violation.

### 19.2 Splits

Six distinct data roles: development, policy-development, certification-calibration, regression, confirmatory holdout, and the permanent production audit. One split doing certification, confirmation, and monitoring launders an underpowered audit into a promotion claim.

### 19.3 Statistics

At least 5 runs per task; task-level bootstrap and Wilson intervals; McNemar or paired bootstrap; Holm–Bonferroni. Detecting δ = 0.03 at 80% power needs about 1,000 items. **A result on fewer than ~150–200 stratified items is a pilot, not a promotion-grade claim.** Flawed-artifact tests (a seeded bad plan, bug, citation, or reference) are mandatory.

### 19.4 Promotion gates

A change is promoted only when all applicable gates pass, in order: objective validity → artifact safety (`L_escape`, `R_accept` within policy) → coverage floors → authority and effects (no invariant violation, stale authority, or unreconciled outcome) → final-quality noninferiority versus the strongest matched baseline → each added piece of machinery earns its keep at matched budget → verifier authority limited to calibrated slices → regression → total lifecycle economics. **Threshold values are deployment policy**, calibrated on the actual workload and bound into the effective policy; they are not architecture.

**Detail:** Vol. I §10; Vol. II §14; Vol. IV (baseline ladder, ablations, experimental contract, open tensions).

**Implementation status — PARTIAL.**
- **BUILT:**
  - fixture evaluation (`evaluate`) and replay with provenance checks;
  - V1.2 grouped partitions, with calibration and holdout sealed and a one-way holdout receipt (these map onto four of the six roles: development, policy-development, certification-calibration, confirmatory holdout);
  - a fail-closed dataset validator;
  - Wilson intervals;
  - a V2 decision gate;
  - CI on Ubuntu and Windows for Python 3.11–3.13.
- **NOT STARTED:**
  - rungs B0, B1, B2, B4–B7;
  - metered budgets;
  - multi-run statistics;
  - the regression split;
  - a production audit stream.
- **Engineering fixtures are labeled as such and excluded from real-task prevalence.** That matches §19.3.

---

## 20. Build order

### 20.1 Principles

1. **Dependency order.** Identity and baseline → authority → isolation → inference → verification economics → memory → learning → promotion → federation. Machine learning waits until the system can trust its own observations.
2. **Veto surfaces precede evidence surfaces.**
3. **First product milestone:** one real slice, one consumer-observed wiring proof, one external boundary canary, and zero autonomous consequential release until the enforcement path works.
4. **Mock models first for authority work.** The first authority question is whether hostile executors can bypass the kernel, not whether an LLM can reason. A laptop proves invariants, not throughput (Vol. II §16.2).
5. **Out-of-order work is quarantined.** *(New in v1.10.)* Machinery built ahead of an unmet earlier exit proof MAY exist only in shadow, and SHOULD NOT be expanded or re-hardened until the earlier proofs exist. Effort goes to the earliest unmet exit proof.
6. **Status is part of the change.** *(New in v1.10.)* A PR that changes a kernel section's implementation status updates that section's status block and the §0.4 dashboard.

### 20.2 Phases and exit proofs

*v1.10 reconciles CORE v1.9 §13 with implementation profile §21. The profile has no memory phase, so v1.10 inserts one from CORE §13 (item 9) as Phase 5; the profile's Phases 5–7 become 6–8. Where the two orders differed, federation follows learning and promotion, as in the profile. Two Phase 0 changes are new in v1.10: the `ModelEndpoint` contract moves forward from Phase 3 so B0 can exist, and the exit proof adds that B0 runs real tasks into the evidence dataset.*

| Phase | Builds | Exit proof | Status |
|---|---|---|---|
| **0 · Semantics, identity, baseline** | registry package + `core_lint`; exact run, artifact, and principal identity; **authenticated** telemetry with a closed schema; typed artifacts and contracts; deterministic gate-runner; `PackCompositionManifest` / `InteractionCertificate` schemas and initial composition-lint registry; `ModelEndpoint` contract *(moved from Phase 3, new in v1.10)*; **B0 single executor** | the same task and artifact are referred to by stable digests and typed contracts across the system, and **B0 runs real tasks end to end into the evidence dataset** *(new in v1.10)* | **PARTIAL — artifact identity, typed contracts, a minimal gate exist; registry, authenticated telemetry, principal identity, composition schemas, and B0 do not** |
| 1 · Authority microkernel | workload identity; typed policy composer + Cedar; PostgreSQL authority state; broker, grants, effect slots, operations; invalidation head + outbox + stream; monitor keys; signed ledger + witness | no tested untrusted principal can cause an authoritative effect outside the broker/grant path | NOT STARTED |
| 2 · Isolation + durable execution | sandbox tiers, default-deny egress; durable workflows; effect reconciliation; content-addressed artifact store; authenticated evidence ingress | crash, replay, and timeout experiments cannot exceed effect cardinality or turn unknowns into success | NOT STARTED (precursors: hard-verifier workspace; SHA-256-named `ArtifactStore` via `run --artifact-store`) |
| 3 · Heterogeneous inference | `ModelRouter`; one frontier and one cheap model; second, vendor-neutral serving path | model substitution changes compute while the authorization and verification interfaces stay intact | NOT STARTED |
| 4 · Verification economics | checklets, adversarial prober, calibrated aggregation, VoI, `CertificationClosure`, `CCH`, successor certificates, `CertificationClosurePlus`, composition linter and `COMP-L*` | a certified terminal-artifact path; exact-context invalidation after mutation; evidence carry-forward only when applicable; issuance of a successor certificate without stale old-context authority; refusal of unresolved modular credit | **PARTIAL — checklets + shadow B3 + measurement program built, ahead of Phases 0–3 (quarantined per §20.1.5)** |
| 5 · Governed memory | lifecycle, attestations, firewall, descendant revocation | no automatic path mutates protected canon; `R_c < 1` | NOT STARTED |
| 6 · Model Factory | trace zones, rights eligibility, curation, root lineage, split locks, propensity logging, router baselines, distillation pilot, verifier calibration | complete lineage for every example and checkpoint; the factory cannot make itself active | NOT STARTED |
| 7 · Governed promotion + production audit | shadow and canary; closure impact; promotion monitor; uniform and targeted audit; epistemic-stability gate; demotion; drift hooks | a candidate cuts cost on a validated slice without weakening a higher bound; recursive evidence stays distinguishable from independently grounded evidence; counterfactual route claims stay supported; and a later incident or epistemic-decoupling signal demotes it cleanly | NOT STARTED |
| 8 · Federation | portable contracts and manifests; authority-home epochs; federated identity; residency-aware policy; release-time revalidation | remote compute can be replaced or lost without creating remote sovereign authority or hidden state | NOT STARTED |

Domain packs and publication integrations are cross-cutting: the coding pack grows with each phase, and a second pack (writing, as the oracle-poor stress case) begins only after Phase 4's exit proof.

### 20.3 Current position and the next three milestones

The repository is a careful **Phase 4 slice built before Phases 0–3**. Its own decision gate is blocked for a structural reason, not a statistical one: with no producer there are no real tasks to measure. Under §20.1.5 the slice is quarantined: no further hardening of the measurement apparatus until Phase 0's exit proof exists.

**M1 — B0 producer slice. Status: NEXT.**
- A Core-owned `ModelEndpoint` contract addressed by semantic role (`frontier_reasoner`, `cheap_executor`).
- One real provider adapter and one deterministic mock.
- A B0 executor: `TaskContract` → replayable context manifest → model call → `coding_bundle/1.0.0` → `VerificationRunner.run()`.
- Telemetry records resolved model identity, prompt-template hash, and metered tokens.
- *Exit proof:*
  - a **consumer-observed wiring proof**: a B0-produced run is ingested by the V1.2 dataset pipeline as a `real_live` record with no manual step, and validated by `validate-dataset`;
  - one **non-hermetic canary** against the real provider, on a schedule;
  - one real task end to end.

**M2 — Phase 0 registry seed.**
- `registry/invariants.yaml`, seeded from the existing safety tests.
- `codes.yaml` and `state_machines.yaml`, covering checklet-observation states (migrating `CheckletVerdict` to the §9.4 set with `requiredness`) and run terminal reasons.
- A closed `telemetry_event.schema.json` with an **authenticated** `producer_principal`. At laptop scale this is a per-principal signing key checked on append, so an unsigned or wrongly signed event is rejected. Workload identity (SPIFFE) replaces the local keys in Phase 1; the authentication requirement itself is not deferred.
- `core_lint verify-manifest | check-event`.
- *Exit proof:* CI fails on an unknown code, an unknown state, a malformed event, or an unauthenticated append.

**M3 — Unblock the V1.2 decision gate.**
- B0 runs on historical commits from at least two repositories (`real_historical`) and on live issues (`real_live`).
- Coverage spans at least two task families and two patch-size buckets, reaching 50 determinate real tasks.
- *Exit proof:* `report-v12` emits a decision other than `COLLECT_MORE_V1_2_DATA`.
- Only then does the B0-versus-B3 comparison (RQ1/RQ2 pilot) become meaningful.

After M3, the next phase is a laptop-scale Phase 1. Run the infrastructure-free subset of the Vol. II §17.2 acceptance suite in-process against a minimal broker and grant store with mock models, using the cases that need no infrastructure. Candidate tests:
- identity non-forgeability;
- grant replay;
- parameter binding;
- artifact mutation after verification;
- self-verification rejection;
- verifier mutation attempt;
- mechanical-failure-to-approval conversion (from Vol. IV RQ12's "must be 0" metric rather than the §17.2 table).

**Detail:** Vol. I §13; Vol. II §16–§17, §21; Vol. III (deployment progression and roadmap).

---

## 21. What the kernel deliberately leaves open

**Not canonical** (deployment- or research-specific; may change without changing the kernel if the replacement passes conformance): the exact frontier provider or model; the exact local checkpoint; prices; the learned routing algorithm; whether a task uses one agent or many; the number of checklets; the retrieval model; the experiment-tracking product; JetStream versus Kafka at scale; NIM versus KServe/vLLM; specialization technique; active-active global authority (Vol. II §22).

**Open research questions** live in Vol. IV, not here: RQ1–RQ15, RQ17, RQ18, RQ26, and the open empirical tensions. They become kernel rules only through §19's promotion gates. A failed experiment is a simplification result.

**Threshold values** — α, κ_min, the ±3/±5 pp gates, κ ≥ 0.6, reject precision 0.90, cost ceilings — are operating proposals until calibrated on the real workload.

---

## Appendix A — Section map (kernel → volumes)

| Kernel | Vol. I (CORE v1.9) | Vol. II (implementation profile) | Vol. III (runtime + factory) | Vol. IV (research) / Sources |
|---|---|---|---|---|
| §1 Separations | §0 | §1.4, CDR-013 | Exec. summary | — |
| §2 Estimands | §1–§1.2, §6.7 | §13.2 | Evaluation framework | RQ2 |
| §3 Transitions | §1.3 | §5, §6, §19 | Normative architecture | — |
| §4 Invariants | §1.4, §13 | §19 | — | E1, RQ15 |
| §5 Policy composition | §1.5 | §4, CDR-002 | Trusted runtime | Source: trusted-runtime |
| §6 Loop and producer | §3, §4 | §9, CDR-006/007 | — | RQ1, RQ4, RQ5, RQ8, RQ9; Source: routing |
| §7 Broker and effects | §4A | §6, §7, CDR-010 | Trusted runtime | RQ10, RQ12 |
| §8–§9 Verification | §5 | §10.1–§10.3 | Verifier factory | RQ3, E1 |
| §10 Aggregation and governor | §6 | §10, §13 | — | RQ2, RQ13 |
| §11 Durability | §6.6 | §5.8, §10.4–§10.9, §18.7–§18.10, CDR-014–016 | Certification durability | RQ18; Source: RQ18 |
| §12 Composition | §2, §12 | §10.10–§10.11, §13.8, §18.11–§18.12, CDR-017 | Compositional assurance | RQ17; Source: RQ17 |
| §13 Contracts | §7.1–§7.5 | §18 | — | RQ6 |
| §14 Memory | §7.6 | §19 (memory firewall) | — | RQ11 |
| §15 Federation | §7.7 | §16.5, CDR-005 | — | RQ14 |
| §16 Telemetry | §8 | §8.3–§8.4, CDR-012 | — | — |
| §17 Runtime and stopping | §8A, §9 | §15 | — | RQ10 |
| §18 Learning | §11 | §11–§13, CDR-008 | Model Factory | RQ26 |
| §19 Evaluation | §10 | §14 | Evaluation framework | Baseline ladder, ablations |
| §20 Build order | §13 | §16, §17, §21 | Deployment progression | — |

## Appendix B — Changes from v1.9

1. **Restructured** into a short normative kernel plus reference volumes; nothing removed (see `README.md`).
2. **Inline implementation status** on every normative section, plus the §0.4 dashboard, measured against `Reusable-Core@30aaa7d`.
3. **Sixth separation** (recursive evidence) promoted into the kernel from the implementation profile and INV-G12.
4. **RQ17 (composition), RQ18 (durability), and RQ26 (epistemic stability)** given normative kernel sections (§11, §12, §18.3). Previously they were spread across companion revisions.
5. **New invariant family `INV-P*`** for compositional assurance (IDs to be assigned in the register).
6. **Governed transitions** extended to name pack/spine activation and learned-component promotion explicitly.
7. **Build order reconciled** across CORE §13 and implementation profile §21 into Phases 0–8 with exit proofs. Memory is inserted as Phase 5 from CORE §13; federation follows learning and promotion; the `ModelEndpoint` contract moves into Phase 0 so the B0 baseline can exist.
8. **Two new build rules:** out-of-order work is quarantined (§20.1.5), and status is part of the change (§20.1.6).
9. **Concrete next milestones M1–M3** tied to the repository's own blocked decision gate.

---

*End of the normative Reusable Core kernel, v1.10.*
