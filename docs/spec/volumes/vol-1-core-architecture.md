> **Reusable Core v1.10 — Volume I: Core architecture detail**
>
> Normative detail beneath the kernel. Formerly *The Reusable Core — Domain-Agnostic Agent Loop v1.9* (CORE).
>
> **Precedence:** the [v1.10 kernel](../reusable-core-v1.10-kernel.md) wins any conflict with this document. Internal references to "v1.9" and to sibling documents by their former names are historical; see the [supersession map](../README.md#supersession-map).
>
> **Fidelity:** everything below the end-of-header marker is the source document reproduced byte-for-byte (`Reusable_Core_Domain-Agnostic_Agent_Loop_v1_9.md`, SHA-256 `94b985a8fb3fe555`).

<!-- v1.10 volume header end -->
# The Reusable Core
### A Verification-First, Risk-Bounded Agent Loop — Domain-Agnostic Architecture, v1.9

> **Status.** Normative domain-agnostic control plane for dynamically composed agentic work. The core governs artifact production, verification, authority, effects, memory, certification, release, recovery, and telemetry. Agents and models are replaceable executors; they do not become trusted merely by being capable, independent, or persuasive. Consequential transitions fail closed unless an authorized monitor validates the exact object under the effective policy and commits through the governed-transition protocol.
>
> **Runtime load boundary.** This document contains only architecture and operational contracts needed to instantiate or operate the core. Historical release notes, research questions, experimental treatments, priors, and unresolved empirical hypotheses are intentionally excluded from the runtime-facing document.

---

## 0. The synthesis claim

> **Agents are optional implementation strategies. The durable core is artifacts, typed contracts, verification-first decision logic, governed authority over consequential transitions, and total-path telemetry. Specialization is supplied by capability-composed domain packs, never by a permanent agent topology.**

The architecture enforces five separations:

1. **Competence is not authority.** `ExecutionCapability` says an executor can perform a class of work. `AuthorityGrant` says a principal may perform a particular action now, on named resources, under a frozen policy.
2. **Production is not verification.** Producers create candidates; verifiers emit evidence and attestations; controllers and governors authorize terminal transitions.
3. **Epistemic authority is not effect authority.** A verdict can deserve substantial trust while its issuer retains no ability to mutate, publish, release, or commit.
4. **Evidence is not truth.** Model agreement, signatures, traces, tests, and deterministic checks each have explicit applicability and validation boundaries.
5. **Optimization is not governance.** Routers and schedulers may propose the cheapest useful next action. They may not mint permission, waive mandatory verification, or release an artifact.

The target is one control plane that can enter unfamiliar tasks, repositories, and execution substrates without inheriting undeclared authority or hidden state. It composes only the machinery a run earns, but the control plane itself is complete enough to mediate every consequential path it permits.

## 1. The keystone objective and its sibling spines

Frame artifact acceptance as **selective prediction with deferral**, but report the exact end-to-end estimands rather than using one quality shorthand.

For each request:

- `A = 1` when the **exact terminal artifact digest** is accepted.
- `V = 1` when that exact artifact received qualifying independent verification before acceptance.
- `W = A·(1−V)` when the artifact is accepted through a certified waiver.
- `B_ref = 1` when the frozen reference protocol says the artifact should not have been accepted.

The waiver quantities are:

- **Waiver coverage:** `κ = Pr(W=1)`.
- **Conditional false-waiver rate:** `R_fw = Pr(B_ref=1 | W=1)`, undefined when `κ=0`.
- **Absolute false-waiver load:** `L_fw = κ·R_fw = Pr(B_ref=1 ∧ W=1)`.

The verified-acceptance path is represented separately:

- `ν = Pr(A=1 ∧ V=1)`.
- `R_v = Pr(B_ref=1 | A=1 ∧ V=1)`.

Therefore the exact bad-accept load is:

```text
L_escape = Pr(B_ref=1 ∧ A=1)
 = κ·R_fw + ν·R_v
```

If a validated upper bound `ε_V` applies to the verified path, then:

```text
L_escape ≤ κ·R_fw + ν·ε_V
 ≤ κ·R_fw + (1−κ)·ε_V
```

The second line is a conservative bound, not the accepted-artifact error rate. Also report:

```text
R_accept = Pr(B_ref=1 | A=1) = L_escape / Pr(A=1) when Pr(A=1) > 0
C_accept = Pr(A=1) acceptance coverage
C_complete = Pr(request reaches a declared terminal disposition)
```

A system cannot claim quality merely by refusing or deferring everything. Promotion and operations reports therefore carry `L_escape`, `R_accept`, `κ`, `ν`, `C_accept`, and `C_complete` together. Verify-all and fail-closed modes are safe fallbacks with `κ=0`; they are not certified waiver policies and do not define `R_fw`.

The reference protocol may be exact, approximate, or human-backed. Every bound is labeled with its oracle class and applicability. In oracle-poor domains, `B_ref` means disagreement with the frozen adjudication protocol—not metaphysical truth.

### 1.1 The sibling spines — one decision pattern, distinct estimands

The selective-decision pattern applies to several governed surfaces, but the losses are not interchangeable and must never be collapsed into one scalar.

| Spine | Decision | Required reporting | Primary control |
|---|---|---|---|
| **Artifact waiver** | accept without qualifying verification | `κ`, `R_fw`, `L_fw`, `L_escape`, `R_accept`, acceptance/completion coverage | calibrated evidence + certification governor |
| **Memory promotion** | make derived memory production-eligible | `κ_p`, `R_fp^(a)`, `L_fp`, utility, contamination propagation, stratified by authority class | lifecycle + promotion authority |
| **External effect** | realize a consequential state change | unauthorized-effect events and UCBs by severity, containment assumptions, reconciliation status | architectural mediation + grants + effect slots |
| **Federated release** | release an artifact produced across a trust boundary | invariant conjunction, noninferiority margins, disclosure and effect reconciliation | declared closure + foreign verification + release controller |

A correct artifact produced through credential exfiltration is still an authority failure. A factually wrong artifact with no unauthorized effect is still an artifact-quality failure. Neither compensates for the other.

### 1.2 The decision hierarchy — lexicographic over declared budgets

The scalar `maximize E[Q] − λ_c·Cost − λ_ℓ·Latency` is **demoted to a sensitivity analysis**. A weighted score lets milliseconds buy back a protected-canon compromise; nothing may. The normative order — constrained optimization with preregistered budgets at each tier, with waiver/elevation paths where the tier itself defines them, not brittle raw-metric lexicography:

```
0. Hard structural invariants (the §1.4 register: mediation, firewall, closure, integrity)
1. Authority feasibility (grants, certificates, always-verify rules, human-only ceilings)
2. Severe-risk chance constraints (U_δ(R_ue,critical) ≤ β_j; contamination R_c < 1; harm strata)
3. Certified selective-risk bounds (U_δ(R_fw,g) ≤ α_g; U_δ(R_fp^(a)) ≤ α_a)
 + coverage floors (κ ≥ κ_min; completion & acceptance floors — the anti-fail-closed-gaming clause)
4. Final-quality noninferiority (vs. matched B0 / M1 / X0 baselines, domain margins)
5. Pareto optimization (total path cost, p95 latency, hard-verifier volume,
 human-review volume, disclosure excess)
6. Scalar utility (sensitivity analysis only; never selection)
```

Promotion rule: promote a change only if it improves the holdout frontier under equalized budgets **and** keeps every certified bound and invariant above it in this hierarchy. `λ_c`/`λ_ℓ` survive as tier-5 exchange rates and as the §8A resource governor's runtime dials — nowhere else.

### 1.3 Governed transitions — one pattern, separate principals, explicit commit semantics

A **governed transition** is any consequential state change: unverified acceptance, memory promotion, authoritative artifact promotion, external effect, federated release, or protected-canon/policy mutation. It may occur only through an **Authorization Monitor** that:

1. validates the exact subject digest, effective-policy digest, certification or authority closure, resource scope, and validity epoch;
2. evaluates a declared `IndependenceProfile` and `OracleProfile` against transition-specific predicates;
3. fails closed on unknown provenance, scope, support, compatibility, policy composition, or invalidation state;
4. writes through the authority ledger under a monitor-specific authenticated principal;
5. proves its invalidation-bus watermark is current before authorization;
6. delegates the actual commit to the broker or another controller that does not share the producer's mutation authority.

| Transition | Monitor | Instrument | Terminal authority |
|---|---|---|---|
| Accept without qualifying verification | Certification governor | `AuthorityCertificate` bound to a `CertificationClosure` | authorize exact artifact acceptance |
| Promote runtime memory | Memory promotion authority | outcome + transition attestations; promotion certificate | change retrieval eligibility/authority |
| Realize an external effect | Runtime tool broker | `AuthorityGrant` + `EffectSlot` + operation record | commit named effect |
| Release across a boundary | Release controller | foreign verification + release-time closure recheck | publish/release exact subject |
| Mutate protected canon, policy, permissions, or root trust | Authenticated human owner; optional dual control | signed protected-tier approval | no automatic path |

#### Governed-transition commit protocol

Every consequential transition follows the same protocol, serialized by `governed_transition` in `state_machines.yaml`:

1. Capture the subject, policy, closure, lease, and invalidation-bus snapshot.
2. Validate the exact subject and all authority preconditions against that snapshot.
3. Resolve policy composition and reject any unresolved contradiction.
4. Reserve the effect slot or terminal-decision slot.
5. Mint a one-use grant bound to the reservation and snapshot.
6. Immediately before commit, recheck subject digest, lease ownership, grant validity, certificate support, and invalidation watermark.
7. Execute through the broker-owned adapter or controller.
8. Obtain an independent effect observation, provider receipt, or terminal artifact observation.
9. Reconcile ambiguous outcomes; never blind-retry a consequential operation.
10. Append the terminal authority record and publish the decision.

Each transition type declares its **linearization point**—the single authoritative moment at which it becomes committed. Validation before that point is provisional. A bus event, lease loss, digest change, or closure change before the linearization point aborts or revalidates the transition.

#### Common-substrate hardening

A shared authority ledger and invalidation bus provide one query surface, but they are also common-mode dependencies. Logical unification therefore does not imply one undifferentiated trust principal. Required controls:

- monitor-specific signing keys and append-only partitions;
- independently witnessed ledger checkpoints;
- durable monotonic bus offsets;
- fail-closed behavior when a monitor's watermark is missing or stale;
- explicit compromise assumptions for the ledger, bus, broker, and evaluator;
- no inherited identity fields as authority;
- no monitor allowed to approve its own ledger write or witness its own checkpoint.

Epistemic authority and effect authority remain orthogonal. Human ownership grants authorization authority for protected transitions; it does not automatically make the human's factual judgment the strongest oracle.

### 1.4 The invariant register — the machine-checkable constitution

The authoritative invariant register is `invariants.yaml`. Runtime code loads the mechanical and architectural rows directly; telemetry violations reference one invariant ID; packs may add namespaced domain invariants and tighten core rules, but may not remove or weaken them.

The register is grouped by enforcement plane:

- **Global (`INV-G*`)** — exact-object authority, fail-closed unknowns, non-compensable harms, no self-attestation, protected control-plane boundaries, monotonic policy composition, typed missingness, and witnessed authority-state freshness.
- **Authority/effects (`INV-A*`)** — complete mediation of authoritative effects, no amplification, terminal mechanical failures, principal separation, effect cardinality, credential isolation, evidence-write authority, isolated compute, and atomic governed-transition commits.
- **Memory (`INV-M*`)** — evidence-first birth, eligibility-before-ranking, protected-canon firewall, provenance-family accounting, and descendant revocation.
- **Certification (`INV-C*`)** — exact closure-bound certificates, mutation invalidation, undefined false-waiver rate at zero coverage, and path-specific causal certification.
- **Federation (`INV-F*`)** — artifact integrity, declared closure, stable logical-effect identity, no stale release, verifier isolation, and disclosure containment.

Enforcement modes are:

- **architectural:** the forbidden path does not exist;
- **mechanical:** deterministic runtime checks reject the transition;
- **statistical:** a permanent audit stream bounds the residual event rate;
- **procedural:** authenticated human or dual-control action is required.

An invariant referenced by prose but absent from the pinned register is unknown policy and therefore fails closed.

### 1.5 Effective-policy composition — monotonic by construction

Dynamic composition is safe only when multiple applicable policy layers combine deterministically. The controller normalizes every applicable core, deployment, pack, tenant, task, and incident policy into an `EffectivePolicy`.

The authoritative merge algebra is `policy_composition.yaml`:

| Policy dimension | Composition |
|---|---|
| permissions, allowed resources, allowed effects, disclosure allowances, network destinations | intersection |
| explicit denials, required gates, always-verify rules, human-review triggers | union |
| authority ceiling, risk tolerance, validity interval, budget ceiling | minimum / most restrictive bound |
| sandbox requirements | security join: the strongest jointly realizable profile |
| canonicalization and schema requirements | exact compatibility or declared adapter proof |
| unresolved contradiction | terminal `policy_conflict` |

Every composition emits:

```text
parent_policy_digests[]
normalized_effective_policy
effective_policy_digest
non_expansion_proof
conflicts[]
```

A generated or learned policy is eligible only if the non-expansion proof shows that it grants no permission, authority, disclosure, resource scope, or waiver region beyond every applicable parent. Unknown keys, incomparable sandbox requirements, empty validity intersections, and contradictory mandatory rules are conflicts—not invitations to choose a convenient interpretation.

## 2. Two layers: control plane + capability-composed domain packs

The **domain-agnostic control plane** is written once. It owns task intake, policy composition, graph control, resource allocation, artifact contracts, principal and lease identity, tool mediation, gate orchestration, evidence fusion, certification, invalidation, recovery, release, and telemetry. It does not decide what makes a code patch, chapter, research synthesis, or asset pack good.

A **domain pack** supplies domain semantics through a required base profile and only the optional capability profiles the domain actually needs:

```text
BaseArtifactPack
OraclePack
EffectfulExecutionPack
IsolatedComputePack
MemoryPack
CertifiedWaiverPack
FederatedExecutionPack
PublicationPack
```

A read-only prose-analysis pack can stop at `BaseArtifactPack + OraclePack`. A coding pack may add isolated computation, typed effects, memory, certification, and publication. A local pack does not carry empty federation fields; a stateless pack does not carry memory policy.

The control plane composes applicable pack and deployment policies through §1.5. Packs may require stronger gates, narrower authority, stricter sandboxes, lower risk tolerances, or more human review. They may never weaken the effective core policy.

## 3. The component model — one system, two vocabularies

The corpus carries two vocabularies. They are not two designs; they are the **producer side** and the **verification side** of one system. The unification is the most important integration move in this document.

| Component class (generic) | Seven-role name(s) | Job | Authority |
|---|---|---|---|
| **Orchestrator / Router** | Orchestrator | Choose path, pack, budget; invoke roles/checklets; stop/escalate | Policy-authoritative; **never authors artifacts** |
| **Producer(s)** | Planner, Architect, Researcher, Coder→**Builder**, Documentor | Decide / synthesize / generate the artifact | Generate only |
| **Constraint extractor** | (folded out of Planner) | Turn request + context into machine-checkable requirements | Read-only |
| **Verification stack** | **Critic dissolves here** | Many narrow **checklets** → calibrated **risk aggregator** | Diagnostic by default; veto only when calibrated |
| **Hard verifier(s)** | (the expensive end of Critic + execution) | High-fidelity adjudication: full CI, human read, claim audit, UE commandlet/runtime | Authoritative; **objective gates outrank judges** |
| **Adversarial prober (breaker)** | (new; verification side) | *Generates* an input/condition that breaks the artifact, instead of inspecting it (§5.5) | Produces evidence; a *confirmed* break is an objective signal |
| **Integration authority** | (bounded slice of Builder) | Integrate ranked findings and bounded patch proposals into the canonical candidate | One authority per artifact scope and revision transaction |
| **Telemetry learner** | (new; cross-cutting) | Learn router, risk, calibration, stopping from traces | Advisory until calibrated |
| **Runtime tool broker** (§4A) | (new; the reference monitor) | Sole path for every external effect: resolve action → validate → decide policy → attach out-of-band grant → confine → mediate | Trusted computing base; **complete mediation, no ambient authority** |
| **Authorization Monitors** (§1.3) | (new; four principals) | Certification governor · memory promotion authority · broker policy · release controller — bind decisions to digests, fail closed, append to the authority ledger | Authorize governed transitions; **distinct principals, never a producer** |
| **Resource governor** (§8A) | (renamed from *budget governor*) | Allocate tokens/latency/cost; **reserve assurance capacity** | Spending + deadlines only; **no waiver authority** |

Three consequences of this mapping:

1. **The "critic" is not an agent — it is the verification stack.** An ungrounded prose-reviewing critic is a liability (intrinsic self-correction degrades reasoning without external signal; Huang et al., ICLR 2024). Re-cast it as *many grounded checklets feeding a calibrated aggregator*. It localizes defects and computes waiver risk; it earns veto power only when its reject precision is calibrated high **and the finding carries a falsifiable trigger** (§5.6).
2. **"Coder" is too narrow — the role is Builder.** It writes code, edits UE5 assets, drafts a chapter, or synthesizes a memo. Same contract, different pack.
3. **Diagnosis and proposal generation may fan out; canonical mutation does not.** Parallel workers may produce bounded, non-overlapping patch proposals. One integration authority per artifact scope and revision transaction mutates the canonical candidate, resolves conflicts, and establishes the resulting digest.
4. **Decisions are evidence-grounded, not confidence-grounded.** A *block* requires a finding that carries a falsifiable trigger; a *waiver* requires affirmative evidence of cleanliness, not the mere absence of a flag (§5.6, §6.1). Authority scales with how checkable the evidence is — the strongest form is one a service can mechanically verify.
5. **Diagnosis and adversarial generation are two modes, not one.** Inspecting an artifact (the layered evaluator, §5) and *trying to break* it (the prober, §5.5) have different error profiles and catch different defects; the system runs both and the aggregator fuses them (§6.3).
6. **Competence is not authority; a monitor is not a producer.** Routing selects an executor because it *can* do the work (`ExecutionCapability`); an Authorization Monitor independently decides what it *may* do, now, on this exact object (§1.3). A verifier emits attestations, never releases; a producer never approves its own output; protected canon/policy has no automatic runtime write path (§7.6). These are structural facts about who holds which authority, not tunable policy.

---

## 4. Control flow — the canonical loop

### 4.1 The loop

```
Task intake
 → Artifact contract normalization + risk/budget tagging
 → Route + domain-pack selection (orchestrator; ExecutionCapability, not authority)
 → Establish principal + compile the action-availability view (§4A; producer sees actions, never credentials)
 → Memory retrieval under eligibility-before-ranking (§7.6; ineligible records never surface)
 → Producer builds candidate (minimum role set)
 → Every external effect → Runtime Tool Broker (§4A; validate → policy → out-of-band grant → sandbox → adapter → reconcile)
 → Parallel checklet bundle (cheap, read-only, structured outputs)
 → Risk aggregator → calibrated p(error) + uncertainty
 → SCHEDULER PROPOSES an action; DECISION space:
 stop_accept → CERTIFICATION GOVERNOR authorizes/overrides (§6.6; never the scheduler)
 ├ verified_accept | certified_waiver (+ audit q)
 └ override → hard_verify | human | fail_closed
 more evidence +EV → ACQUIRE next checklet / escalate producer (VoI, §6.4)
 else, in budget → HARD VERIFY (execution / claim audit / commandlet)
 ambiguous/high-impact/disagreement → HUMAN
 → Bounded reviser (only on ranked, high-value findings) (mutation invalidates prior verification unless proven-preserving, INV-C2)
 → Best-so-far selector (keep best *validated* iteration, not last)
 → [boundary-crossing only] effect reconciliation → evidence manifest → foreign verification → release-time closure recheck (§7.7)
 → Post-run memory capture → candidate → verify → canary → promote (§7.6; success alone never promotes)
 → Telemetry (authority ledger + invalidation bus) + learning loop
```
The local-only path skips the broker's effect adapters, the boundary steps, and memory promotion — the thin default loop (§4.3) stays thin. Governance machinery activates on the transition that needs it, not on every task.

### 4.2 Agents vs services — the load-bearing distinction

**Agents decide, synthesize, generate. Services verify, execute, cache, compare, store.** Most of what looked like "critic" or "documentor" work is actually *services*: running tests, resolving citations, validating schemas, diffing artifacts, measuring cost. Services are deterministic, cheap, and not subject to judge bias. Push everything you can across the agent→service boundary. The largest single failure mode in long-horizon agent systems is lossy free-text handoffs and opaque failures — services with typed I/O attack that directly.

### 4.3 The default loop is thin; expansion is conditional

The strong single agent (same tools, same context, same retrieval) is the **null hypothesis every added agent must beat.** The default loop is:

```
orchestrator → planner → builder → grounded verifier
```

Expand only on a measured trigger:

| Invoke | Only when |
|---|---|
| **Planner** (separate from orchestrator) | Multiple constraints/deliverables, competing subgoals, or decomposition quality measurably determines success. Otherwise fold into orchestrator. |
| **Architect** | Real interface/dependency/world-consistency/performance complexity (multi-file, schema migration, world bible, asset graph). Remove for linear single-artifact tasks. |
| **Researcher** | External evidence/source quality determines task quality. Remove for closed-book/local tasks. |
| **Critic→checklets** | After objective gates run, or when subjective residual quality matters, or confidence is low. Never review what deterministic checks already validated. |
| **Documentor** | The deliverable explicitly *is* a doc/RFC/changelog. Otherwise it is a finalization transform, not an agent. |

**Effort scaling** (Anthropic's rule, generalized): trivial → single agent, no decomposition; standard → planner + builder (+ checklets); complex/system-design → add architect; breadth-first → parallel producers. The cost of getting this wrong is real: multi-agent runs ~15× the tokens of a single chat, and that multiplier must be justified by the task's structure.

### 4.4 Why thin-by-default is evidence-based, not taste

- Multi-agent decomposition **wins on breadth-first parallel work** (Anthropic's research system beat single-agent Opus 4 by **90.2%** on its internal research eval) but **loses on tightly-coupled reasoning under matched compute** — coding is explicitly "tightly interdependent."
- MAST (1,642 traces, 7 frameworks, κ=0.88) found multi-agent systems fail at a **41%–86.7%** rate, clustering into System Design **41.77%**, Inter-Agent Misalignment **36.94%**, Verification/Termination **21.30%** — and the authors' best tactical fixes (+9.4% role-spec, +15.6% verification) were judged "insufficiently low for real-world deployment," motivating *structural* redesign.
- Dynamic routing is a proven cost lever: RouteLLM reaches **95% of GPT-4 quality at 26% GPT-4 calls** (~48% cheaper), and **14% of calls** (~75% cheaper) with judge-augmented routing data.

The architecture follows task structure. It does not assume more agents are better.

### 4.5 Producer policy — generation is not a black box

Verification-first is not verification-only. The loop can only verify or waive a candidate that is worth verifying; a system that generates one mediocre candidate and revises it forever just burns budget discovering that the first branch was bad. So the producer side gets its own policy: construct the context deliberately, pick the cheapest production mode that can satisfy the contract, generate diversity when variance warrants it, and **select the best *validated* candidate — not the most polished or most confident one.**

**Context is a manifest, not a prompt blob.** Each producer call receives an explicit, replayable context manifest (task brief, artifact contract, requirements, prior artifacts *by reference*, retrieved snippets with trust levels, domain-pack + template versions, a context budget). Passing artifacts by reference rather than informal summary is the direct attack on handoff loss (§7.4); making the manifest explicit is what lets you later tell whether a failure came from generation, context, tools, or verification. Select context by expected marginal value, in priority order — user constraints → contract/acceptance criteria → domain prohibitions → relevant prior artifacts → needed evidence → examples/templates → optional scaffolds — never "include it because it exists."

**Retrieval is a producer concern too, not only a verifier (L4) one.** When artifact quality depends on codebase state, world continuity, prior designs, or source evidence, the producer retrieves, and records what it pulled and at what **trust level** (authoritative / supporting / untrusted / adversarial). Untrusted or retrieved content is *subject matter to inspect, never instructions to the system* — this is the producer-side half of the threat model (§8A).

**Production modes** (orchestrator picks the cheapest that fits): single-pass (simple, low-risk, easily verified) · retrieve-then-generate (external facts/state matter) · plan-then-generate (dependencies/sequencing) · tool-augmented (tools materially improve correctness) · best-of-N (high variance *and* verification cheaper than manual generation) · revise-existing (a prior candidate is close, defects localized).

**Best-of-N is the default diversity mechanism for high-variance generation — but only when selection is stronger than generation.** It is not "try N times"; each candidate varies along an intentional axis (planning posture, architecture strategy, research strategy, narrative mode, patch strategy), and every run feeds a **selector** that consumes gate results, checklet findings, requirement coverage, residual risk, and cost. N scales with risk/variance/budget: 1 for low-risk deterministic, 2 standard, 3 high-variance subjective, 3–5 important design/research; for high-impact-but-expensive work, generate *fewer* and verify *harder*. Selector ranking: reject candidates failing non-waivable gates → higher requirement coverage → lower calibrated residual risk → fewer high-severity findings → lower revision burden → cheaper only to break ties. The selector **preserves a validated best-so-far across revision rounds** (§9); a later draft never auto-supersedes an earlier validated one.

**Resample vs. revise** is an explicit decision. Revise when defects are localized, gates mostly pass, coverage is high, findings are actionable, and prior revision didn't regress. Resample (or replan) when the candidate misses the core task, the structure is wrong, many defects share a root cause, revision would rewrite most of it, or the candidate is overfit to judge/checklet preferences. **Hard rule: do not spend repeated revision budget on a candidate whose artifact contract is wrong** — regenerate or replan. (This is the §11 risk-model's eventual job: predict revision gain so this decision is learned, not guessed.)

**The master switch is verifier soundness (the §5.7 oracle ceiling), then task variance, then budget.** This is the most important calibration the producer loop needs, and the evidence is strong:
- *Sound oracle (tests, citation-entailment, deterministic system/continuity validators):* end-to-end success = **coverage**, so best-of-N rides the coverage curve, which grows log-linearly in N (repeated-sampling regime — SWE-bench Lite 15.9%→56% at 250 samples with a verifier). Scale N **only where the model "sometimes succeeds"** (per-sample p roughly 0.1–0.9); at p≈1 one sample suffices, at p≈0 resampling is wasted (revise-with-feedback or upgrade the model). Push temperature up (~0.8–1.2) to maximize coverage.
- *Noisy verifier (prose reward model / LLM judge):* the **selector caps success regardless of coverage**, and there is no free lunch — a nonzero verifier false-positive rate imposes a hard accuracy ceiling that more compute cannot beat, the FP rate *rises* with N, and with any cost for false positives the **optimal N is finite and small (often ≤5–10), sometimes zero**. Worse, single-sample accuracy correlates with FP rate, so resampling a weak model cannot reach a strong model's single-shot quality, and large N becomes an efficient *search for reward-hack exploits* (length, verbosity, sycophancy) as the gold reward peaks then falls. Keep N small (≤~5), temperature moderate (~0.7), spend the rest of the budget on revision and on improving the verifier + human-in-the-loop.

So the budget split tracks difficulty: easy/near-correct → sequential revision; hard + high-variance + sound oracle → parallel best-of-N; and per-prompt compute-optimal allocation (predict difficulty, allocate accordingly) beats naïve uniform best-of-N by up to ~4×. **Mixed domains use a two-stage pattern**: best-of-N gated by the *sound* validator as a hard filter, then *revise* the survivor on the noisy dimension with small-N judge selection + a human check — use the oracle where it's sound, revise where it isn't. Diverse verifiers (a small multi-verifier panel) push the selector ceiling up where single-RM/self-consistency selection plateaus (§6.3). Decision triggers: FP→0 ⇒ increase N, lean parallel; judge agreement <~75% (prose) ⇒ N→1, lean revision, escalate; coverage ≥~95% ⇒ stop scaling N (the residual is selection-bound, not coverage-bound).

### 4.6 Plan-level orchestration — typed task graphs and selective recomputation

The canonical loop verifies one artifact; non-trivial work is a graph of dependent artifacts. The planner emits a bounded task graph whose nodes declare:

```text
node_id
artifact_type
artifact_scope
integration_authority
depends_on[]
blocks[]
acceptance_criteria[]
required_gates[]
required_checklets[]
per_node_budget
policy_inputs[]
```

Node lifecycle is governed by `task_node` in `state_machines.yaml`. The closed state set is:

```text
pending · ready · running · blocked · human_wait · passed · failed
waived · advisory_only · human_approved · stale · abandoned
```

Only `passed`, validly `waived`, `advisory_only`, or `human_approved` satisfy a dependency, and each has different semantics. A human-approved node records the approving principal and exact digest. A waived node records the certificate. Advisory-only means the downstream consumer may proceed only where the dependency was declared non-blocking.

Checklet execution is not represented by node absence or an empty findings array. Every planned checklet produces a `CheckletObservation` with:

```text
requiredness: mandatory|conditional|optional
state: not_selected|not_applicable|running|clear|finding|abstain
 |mechanically_invalid|outcome_unknown|cancelled
selection_reason
scope
evidence_family_ids[]
```

`not_selected`, `not_applicable`, `abstain`, `cancelled`, and `outcome_unknown` are distinct. None counts as affirmative evidence of cleanliness. A mandatory or triggered-conditional checklet ending in `outcome_unknown`, `mechanically_invalid`, or `cancelled` blocks its scope until policy routes it to retry, replacement evidence, human review, or fail-closed termination.

Each downstream artifact records the exact upstream digests and requirement-trace edges it consumed. An invalidation event marks only causally affected nodes `stale`, using the declared dependency semantics. Revalidation may reuse unaffected artifacts; false-staleness is measured so selective recomputation must beat an end-to-end rerun rather than merely appear sophisticated.

Scheduling obeys these rules:

- run cheap fail-fast gates before expensive generation;
- prioritize critical-path and high-fan-out nodes;
- parallelize only non-overlapping production scopes or independent verification;
- reserve mandatory verification budget before generation expansion;
- route failures to the earliest causal node;
- prefer bounded local graph repair over full replanning;
- never treat lack of remaining activity as a terminal reason.

Parallel workers may prepare bounded, non-overlapping patch proposals. **One integration authority per artifact scope and revision transaction** mutates the canonical candidate, resolves conflicts, and owns the resulting digest. This is the singularity that matters; proposal generation need not be artificially serial.

Partial completion is a first-class terminal disposition. The release package states which artifacts are accepted, waived, advisory, stale, human-pending, failed, or abandoned, and why. A run ends only through a registered terminal state and attributable terminal reason.

#### Invalidation bus

Authority decays on event, not merely age. The bus carries artifact, model, tool, schema, policy, canon, incident, lease, revocation, and drift events. Subscribers react according to binding:

- changed upstream artifact → affected task nodes `stale`;
- changed memory premise → `needs_revalidation` or `quarantined`;
- changed action implementation → grants revoked or expired;
- changed certification closure → certificate `unsupported`;
- stale execution closure at release → `stale_at_release`.

TTL is a supplementary exposure limit. It never overrides a known breaking event. Every monitor records the bus watermark used for its decision and fails closed if that watermark cannot be proven current.

## 4A. The runtime tool broker — effect mediation and isolated computation

The model, agent, plugin, and retrieved content are untrusted decision inputs. The security boundary is not “prevent all bad reasoning”; it is:

```text
compromised reasoning ⇏ unauthorized authoritative effect
```

The broker enforces four distinct abstractions:

- `ExecutionCapability`: what a frozen executor can do;
- `ActionContract`: the semantic operation available to request;
- `AuthorityGrant`: what a principal may do on this invocation;
- `ResourceHandle`: the exact object or destination the action may affect.

### Typed production actions

Typed named actions are the only interface to authoritative state and external systems. The action registry does not expose raw host shell, generic interpreters, arbitrary subprocesses, unrestricted Git, raw SQL, arbitrary URLs, ambient credentials, or host paths. Trusted adapters may use those mechanisms internally, but the requesting principal receives only the declared semantic action.

Resources and destinations are policy objects, not strings: `workspace_file:<digest>`, `repository:<id>`, `service:github-api`, `release_target:staging`. Authority binds to the action implementation digest and exact or bounded parameter envelope.

### Isolated compute cells

Open-ended code execution remains necessary for real repository work. It is therefore a first-class **isolated compute cell**, not a disguised production action:

```text
arbitrary shell/code: allowed inside the cell
filesystem: ephemeral or branch-local
ambient credentials: none
external network: denied by default; named mediated reads only
authoritative shared writes: denied
resource limits: mandatory
declared read inputs: content-addressed
outputs: leave only through validated artifact export
```

The cell may compile, test, transform, and mutate its private workspace. Those are **ephemeral internal mutations**, not authoritative effects. Promoting a patch, writing shared state, publishing, pushing, messaging, releasing, or changing permissions requires a separate broker action and governed transition. A platform that cannot realize the required isolation profile marks the action unavailable; it does not silently downgrade it.

### Grants, principals, and effect adapters

Authority is attached out of band. An `AuthorityGrant` binds issuer, broker audience, principal, role, run, action ID/version, implementation digest, resource handles, parameter digest or envelope, sandbox and network profile, effective-policy digest, not-before/expiry, maximum uses, effect slot, operation ID, and invalidation watermark.

High-risk effects are broker-owned. Plugins and agents may prepare a request, but never receive the credential that commits deploys, releases, payments, external messages, repository pushes, permission changes, secret rotations, or publications.

Producer, verifier, integration controller, certification governor, and release controller are separate principals with distinct credentials, action subsets, writable mounts, network policies, output namespaces, and audit identities. A producer cannot issue a verdict or release. A verifier cannot mutate the candidate or release. A controller consumes valid evidence and performs the governed transition.

### Effect slots and reconciliation

An **effect slot** represents one authorized semantic intent and maximum commit cardinality `m(h)`. An **operation record** represents one transport attempt and its retries:

```text
(slot, operation, action, digest(params), principal, target)
```

Same operation and same digest joins the authoritative result. Same operation and different digest is an idempotency conflict. A new operation ID does not create a new semantic intent. `N_commit(h) ≤ m(h)` is enforced at all times.

An ambiguous provider outcome becomes `outcome_unknown`. The system reconciles against provider receipts and independently observed state; it never blind-retries a consequential operation. The claim is at-most-one authoritative commit per logical effect, or an explicit unresolved state—not universal exactly-once execution.

### Failure and observation

Mechanical errors are terminal and non-elevatable. Parser failures, unknown actions, capability mismatches, scope violations, forbidden resources, network violations, hard-denied surfaces, policy conflicts, and idempotency conflicts create no effect and no approval prompt. Human approval applies only to valid semantic effects explicitly declared elevatable by policy.

The broker's own trace is not sufficient proof that containment held. Independent observations cover:

- effect state;
- resource exposure;
- authorization decision;
- downstream provider receipt;
- terminal artifact or release state.

`broker=denied ∧ state=changed` is a containment bypass.

Telemetry and ledger writes are themselves effects. Production evidence requires an authenticated producer principal; test and hermetic execution environments must be physically unable to append to production ledgers. Environment variables and inherited `run_uid` values are claims to validate, not authority.

The containment claim applies only under complete mediation, unforgeable non-amplifiable grants, sound action specifications, effective isolation, correct policy composition and issuance, current invalidation state, and independent observation. When an assumption fails, the claim does not apply.

## 5. The verification stack (verification-first gate)

Use the **cheapest, strongest, least-gameable signal that is actually available** for each quality dimension. The hard ordering below is not aesthetic — it is what keeps a subjective judge from overruling an objective failure.

| Layer | What it gates | Semantics |
|---|---|---|
| **L0 — Task/contract validation** | Task type, requested artifact, constraints, budget, risk level, pack, required outputs | Ambiguous/high-impact → clarify or human-triage *before* any agent runs |
| **L1 — Deterministic validation** | Schema, required sections, naming, exact formatting, missing fields, dependency refs, budgets, prohibited patterns, required citations, package structure | **Fail-closed.** Total function artifact→{pass,fail}. |
| **L2 — Static analysis** | Lint, types, dependency cycles, missing refs, security scans, config validation, asset-graph / continuity-graph checks | Severity-tiered: high-confidence/high-severity *blocks*; lower findings *inform* the aggregator |
| **L3 — Execution & simulation** | Compile, unit/integration/property/fuzz tests, scenario replay, runtime smoke tests, commandlet validation, executable doc examples | Strongest behavioral signal whenever an oracle exists |
| **L4 — Source/claim/citation** | Source resolves, quote-span matches, claim is supported, not contradicted, fresh enough, diverse enough | Claim-level support, not "sounds factual." Critical-claim gating. |
| **L5 — Residual LLM judging** | Only the *subjective residual*: clarity, coherence, synthesis quality, narrative, usefulness, style fit | Calibrated judges only; never overrules L1–L4 |
| **L6 — Human review** | High-impact, ambiguous, evaluator disagreement, calibration sets, holdout labels, creative final quality | Humans *where they matter most*, not everywhere |

### 5.1 Push the deterministic/subjective boundary

The central engineering move: **decompose subjective rubrics into checkable sub-criteria** (G-Eval's insight: more, simpler sub-criteria → more robustness, less bias/randomness). Many decompose straight into deterministic checks — "is the API example runnable?" becomes a compile test; "does every claim cite a source?" becomes a reference-resolution check. A dimension is *deterministic-eligible* if it can be expressed as a total function artifact→{pass,fail} with no human-preference judgment. Everything else routes to the judge. (Caveat: schema validation checks *syntax, not semantics* — continuity/factual assertions belong in L2/L4, not L1.)

### 5.2 Resolving the pairwise-vs-pointwise tension (the one real disagreement in the corpus)

The source documents disagree on judge mode. They reconcile cleanly once you split by **the judge's job**:

| Job | Mode | Why | Mitigations |
|---|---|---|---|
| **In-loop gating** ("does this clear the bar?") | **Pointwise rubric**, dimensions scored independently | Absolute scores flip ~**9%** under distractors; per-item, thresholdable, less position-sensitive | Criteria injection (+~3pp), decomposition, calibration to κ≥0.6 |
| **Selection / best-so-far / A-B / ablation** ("which is better?") | **Pairwise** vs *mediocre* anchors → Bradley-Terry | Comparative framing tracks human preference better for ranking | But pairwise flips ~**35%** under distractors — so armor it (below) |

The *Layered Verification Gate* doc favors pairwise because it is specifically about the end-of-loop **selection** gate — and pairwise is correct *for that job*. Both modes pass through the same calibration discipline. Never mix modes within one dimension (it makes the judge contradict itself).

### 5.3 Judge hardening (applies to both modes)

| Bias | Magnitude | Mechanical mitigation |
|---|---|---|
| Position/order | ~10–15pp swing (≤0.04 in some studies) | Evaluate both orders, average; mark swap-disagreements as ties; track swap-disagreement rate as judge health |
| Verbosity/length | ~10–30pp | Length-controlled win rates / normalization |
| Self-preference | ~10–25pp (e.g., 82%→30%) | **Multi-family panel (PoLL)** — never judge with the generator's family; cuts self-preference >50% |
| **Style-over-substance** | **dominant: 0.76–0.92** | Dimension decomposition, rubric-anchored prompting, explicit style-bias test set |
| Sycophancy/anchoring | — | Hide model identity; CoT rationale *before* verdict |
| Calibration drift | several points on a fixed set | Pin (judge_id, rubric_version, prompt_hash); recalibrate on every judge-model bump |

**Panel (PoLL):** a 3-model disjoint-family panel correlates better with humans than a single frontier judge, has less intra-model bias, and is **>7× cheaper.** **Aggregate pairwise via Bradley-Terry, not online Elo** (BT is the MLE of the win-rate model — more stable, tighter CIs; the method LMArena adopted after finding Elo too order-dependent). Report **Cohen's/Krippendorff's κ, not raw % agreement** — correlation can be high while κ is poor (systematic bias). **Gate any judge used in a promotion decision at κ ≥ 0.6 vs. humans.** Calibrate against a *small expert gold set* and statistically debias with **PPI/PPI++ or Rogan–Gladen** — treat the judge as a noisy sensor: measure its sensitivity/specificity on gold, then produce provably unbiased estimates. Reliability is ceiling-bounded by the task's inter-rater agreement (e.g., the best off-the-shelf creative-writing judge reaches only 73% human agreement; a trained reward model 78%) — which is exactly why creative domains lean harder on L6.

**Judge reliability is not monotonic with model size, and strong judges fail on hard objective items.** A fine-tuned or reasoning-specialized judge can beat a larger generic one, and in some code-review studies a smaller cheaper model wins — reliability is an empirical property of the *judge-task pair*, not the base model's leaderboard rank. The cautionary anchor: on JudgeBench's hard objective-correctness pairs, many strong judges score only slightly above random, and code-judging benchmarks (CodeJudgeBench) show heavy order-sensitivity even in modern models. Select and calibrate the judge *for the task*; never promote one because its base model tops a leaderboard.

### 5.4 The gate-runner (services side)

A single `gate run <artifact>` entrypoint: loads a **hash-pinned versioned ruleset**, executes tiers in order with **early exit**, emits one JSONL event per check, returns standard exit codes (0 pass; non-zero = first failing tier), supports `--tier` (subset) and `--report` (machine-readable). This is the established CI quality-gate pattern (each gate `allow_failure: false`); schema-derived testing (Schemathesis-style) already demonstrates "derive checks from schema, return exit codes, export JUnit-XML" with near-zero per-endpoint maintenance.

### 5.5 Adversarial generation — the second verification mode

The layered evaluator above is entirely *diagnostic*: it inspects the artifact. There is a second, complementary mode — **adversarial generation**, where a *breaker* actively searches for an input, state, or condition that makes the artifact fail, instead of reading it for defects. This is not a checklet; it is a producer pointed at destruction, and it earns first-class status for one reason: **passing every inspection and execution gate is not proof of safety.** The security-repair literature is blunt that developer tests verify *expected* behavior and not adversarial inputs — a patch that passes all tests can still be exploitable — so an artifact that clears L1–L5 can still harbor an unprobed failure mode. Generation finds the failure modes inspection never thought to look for.

Properties: it runs **in parallel with** the diagnostic stack (two lenses with different error profiles, §6.3); it is **risk-triggered** (you do not spawn a breaker swarm on a trivial change — that is the κ/effort-scaling lever, §4.3); and its output is **evidence** — a concrete trigger, ideally executable (§5.6). The domain supplies the breaking technique: code → *differential / property-based / metamorphic testing and fuzzing*; research → contradiction-seeking and source-falsification; writing → adversarial style/verbosity bait and contradiction probes. A *confirmed* break is an objective signal that outranks any judge; a merely *claimed* break is refuted-by-default unless it carries a reproducible trigger (§5.6).

Two related modes sit on the generation side of the line. **Debate / multi-agent critique** pits competing arguments or lenses against each other to surface asymmetries a single inspector misses — strong for hard reasoning, but exposed to correlated bias and confident liars, so it earns authority only through the same evidence/calibration gates (§5.7). **Process verification** (step-level / PRM-style) checks the *trajectory* rather than the final artifact — verifying intermediate reasoning steps or handoffs — and is the natural verifier for reasoning-heavy packs; it is the verification-side complement to handoff-loss tracking (§7.4).

### 5.6 Evidence-grounded findings — authority scales with evidence

A finding is not actionable because the verifier is *confident*; it is actionable because it carries *evidence*. The operating rule (the collab-kit "reject unless you can point to the exact locus and a concrete trigger," generalized): a flag earns **block-authority** only when it names a falsifiable trigger, and authority rises along an **evidence ladder**:

```
claim-only → advisory at most (a confident assertion is still just an assertion)
located → + the exact locus (file/line/span/scene-fact)
triggered → + a concrete condition that demonstrates the failure
executable → + a runnable check the system itself can verify ← strongest
```

An **executable** trigger is the strongest form because it converts an L5 judgment into an L3 oracle: a finding with a runnable repro is no longer a calibration problem, it is a pass/fail. Push findings down this ladder wherever the domain provides an oracle (code: a failing test; writing: the continuity engine or a blind-attribution check). The finding format that supports this is CriticGPT's — a claim bound to a quoted span — extended with the trigger. This is also the precision mechanism behind reject-by-default review: requiring the trigger is what kills the plausible-but-wrong findings (the "nitpicks and hallucinations" that make naive LLM review useless), and the precision gain from the requirement is itself something to measure (§10).

### 5.7 Verifier authority — evidence, oracle validity, independence, and staged rollout

A verifier earns authority through four gates:

1. **Schema gate:** malformed or structurally incomplete outputs become `mechanically_invalid` or `abstain`.
2. **Evidence gate:** findings must carry the evidence required for their claimed authority level.
3. **Oracle gate:** the oracle must be applicable and sufficiently validated for the claimed property.
4. **Calibration gate:** residual model judgment must meet the severity- and slice-specific operating threshold.

Authority is not computed from a single “independence class.” Independence and oracle strength are multidimensional profiles defined in `verification_profiles.yaml`.

#### IndependenceProfile

At minimum, record:

```text
principal_separation
model_family_separation
prompt_lineage_separation
prior_conclusion_exposure
evidence_family_separation
toolchain_separation
execution_environment_separation
organizational_separation
```

These axes are not totally ordered. A same-model verifier with a fresh executable reproduction may be stronger for a particular claim than a different-model reviewer that inherited the same false requirements and evidence. Transition policy therefore evaluates explicit predicates over the profile.

Examples:

- self-approval fails any consequential transition because principal separation and evidence-family separation are absent;
- a different provider with clean context improves model and prompt separation, but does not prove evidence independence;
- two reviewers using the same retrieved source incident remain one evidence family;
- an isolated deterministic execution can supply strong claim evidence while still requiring validation of the test specification and harness.

No automated principal may self-declare stronger independence. The profile is computed from executor identity, prompt lineage, context digests, evidence lineage, tool outputs, environment identity, and organizational ownership.

#### OracleProfile

A deterministic check is repeatable, not infallible. Every oracle records:

```text
oracle_class: model_judgment|retrieval|executable|formal|expert_adjudication
repeatability: stochastic|controlled|deterministic
specification_soundness: unknown|reviewed|validated
implementation_conformance: untested|canary_checked|validated
applicability: exact|conditional|heuristic
known_false_accept_rate
known_false_reject_rate
validated_slices[]
```

A deterministic validator can still encode the wrong rule, run against the wrong environment, validate a writer rather than a consumer, or become stale. Its result is mechanically decisive only within its validated specification and applicability boundary. Mutation tests, differential checks, consumer-observed wiring tests, live boundary canaries, or independent oracle review establish conformance.

Human or domain-owner involvement is not the top rung of one epistemic ladder. A human owner may possess protected-transition authority while offering weak or biased factual judgment. Expert adjudication is represented as an oracle class; protected authorization is represented separately as an effect-authority rule.

#### Domain ceiling and rollout

The domain's strongest available oracle limits verifier authority:

| Domain shape | Typical evidence | Default ceiling |
|---|---|---|
| executable or formal oracle | failing reproduction, checker, proof validation | auto-block may be justified within validated scope |
| verifiable structure with partial oracle | schema, static proof obligations, reranking | high-confidence block only for covered properties |
| oracle-poor or subjective | source spans, calibrated human preference | advisory, search, abstain, or human review |

Every verifier progresses through `shadow → advisory → scoped_auto_block`. Promotion applies only to validated slices and is continuously monitored. Drift, invalid wiring, unsupported oracle status, or precision loss demotes the verifier automatically.

### 5.8 Instantiation proofs — wiring, boundaries, evidence families, and typed incompleteness

A component is not implemented merely because its code exists or its own unit tests pass. Load-bearing instantiation requires four proofs.

**Consumer-observed wiring proof.** A test drives the production entry point and an independent consumer observes the intended effect. A writer asserting on the state it just wrote is zero evidence that any reader, controller, or release path consumes that state.

**External-boundary contract proof.** Every provider API, broker, browser, queue, or other external wire has at least one scheduled non-hermetic contract check, or the boundary is declared unverified and nothing load-bearing may rest on it. Mocks validate expected shapes; they cannot discover unmodeled wire behavior.

**Evidence-family accounting.** Multiple models or reviewers that share prompt lineage, evidence, prior conclusions, or tool outputs may still constitute one evidence family. The `IndependenceProfile` determines which dimensions differ; record count never substitutes for independence.

**Typed incomplete outcomes.** Every planned checklet produces a `CheckletObservation`. Failure to finish is `outcome_unknown`, `cancelled`, or `mechanically_invalid`—never an empty findings array. Whether that blocks depends on the checklet's frozen `requiredness` and scope. Confirmed findings survive unrelated lane failures and remain attached to the artifact until explicitly resolved, superseded, or invalidated.

Requirements are checked by positive traceability, not absence of raised defects. Each required contract item must have a downstream realization, authorized waiver, or explicit unresolved state.

## 6. The risk aggregator + waiver policy (the savings engine)

This is where the "fewer hard verifications" goal is actually delivered — with a *bounded* risk, not a hopeful one.

### 6.1 Calibration → guarantee

If the aggregator outputs a calibrated `s ∈ [0,1]` with `s = Pr(E=1 | s)`, and the policy waives whenever `s ≤ τ`, then:

```
R_fw(τ) = E[s | s ≤ τ] ≤ τ
```

and if tail calibration is imperfect but bounded by `ε_cal` near the threshold:

```
R_fw(τ) ≤ τ + ε_cal
```

**The operational lesson: tail calibration near the low-risk threshold matters more than a single global ECE number.** Temperature scaling is usually the strongest simple post-hoc calibrator; beta calibration when the score family is poorly matched; deep-ensemble / MC-dropout heads give the uncertainty you turn into a conservative *upper bound* `u(s)` for the waive test.

**A waiver is evidence-grounded, not score-grounded — and not self-authorized.** A calibrated score and cleared checks make a candidate *eligible* to waive; the **certification governor** (§6.6) *authorizes* the terminal acceptance, bound to the exact artifact hash. This is the §1.1 epistemic-vs-effect split inside the savings engine: the aggregator produces evidence, the governor holds the authority, and a scheduler reward term is never a substitute for the certificate. `s ≤ τ` is necessary but not sufficient: a low risk score that rests on the *absence of checking* (nothing looked, so nothing flagged) is not a waiver — it is an unexamined case, and it routes to evidence acquisition (§6.4), not to accept. A waiver requires *affirmative* evidence of cleanliness: a sufficient, diverse set of checks that actually cleared, or recovered evidence in the uncertain band. This is the **ReCoVERR principle** applied to the waive decision — when uncertain, recover supporting or contradicting evidence and decide on *that*, rather than abstaining outright or waiving on a bare threshold. It is the symmetric partner to §5.6: blocks need evidence, and so do waivers.

**The oracle that defines the loss must itself be sound, or the guarantee is vacuous.** R_fw is only as meaningful as the check that decides "error" — and a *similarity-based* oracle is not sound: embedding-based hallucination detectors that look strong on synthetic data collapse toward ~100% false-positive at high recall on real model hallucinations, while a reasoning judge or true retrieval check stays usable (~7% FP). So the oracle behind any waiver guarantee must be a reasoning judge or a real retrieval/execution check, never an embedding-similarity proxy; the proxy's own error floors R_fw, and a bad proxy makes the bound meaningless before any calibration begins.

### 6.2 The aggregator is an evidence-fusion model, not a score-averager

| Family | Best use | Weakness |
|---|---|---|
| OR / AND / majority rules | Fast bootstrap; easy to certify | Ignores interaction strength + calibration |
| Naive-Bayes / likelihood-ratio | Binary checklets with stable TPR/FPR | Overconfident under correlation |
| **Logistic stacking / GBDT** | Rich trace meta-features, nonlinear interactions | Needs labeled traces + careful calibration (**usually best practical accuracy**) |
| Dawid–Skene / GLAD | Checklets-as-noisy-annotators; per-checklet competence + difficulty | EM training; weaker with dense features (**use it to expose drifted checklets**) |
| Conformal / LTT wrapper | Final waive/verify thresholding | Needs dedicated calibration data (**this is the guarantee layer**) |

Recommended recipe: **train a flexible discriminative aggregator → calibrate it → wrap the waive decision in a finite-sample controller**, and add a Dawid–Skene/GLAD layer when per-checklet monitoring matters.

### 6.3 Diversity is the whole game (fusion math)

Under conditional independence, each checklet multiplies the posterior odds by its likelihood ratio — so **redundant checklets exaggerate apparent gain**. For `k` identical checklets with hit rate `a` and false-alarm rate `b`, OR-to-verify (waive only if all clear) gives:

```
R_fw^OR(k) = π(1−a)^k / [ π(1−a)^k + (1−π)(1−b)^k ]
```

Illustrative (`π=0.2, a=0.8, b=0.2`): false-waiver ≈ **5.9% → 1.5% → 0.39%** for `k = 1, 2, 3`. That near-exponential gain is *real only when checks are conditionally diverse*; positive correlation collapses it, which is why Dawid–Skene/latent-factor models beat naive independence whenever checklets share blind spots. The deepest diversity axis is **diagnosis vs. generation** (§5.5): a diagnostic checklet and an adversarial prober have maximally different error modes, so fusing them buys more than adding a redundant checklet — but the complementarity is a hypothesis to *measure* (unique-catch rate per lens), not assume (§10).

**The dark side of the same arithmetic: decomposition *without* calibration is worse than one broad critic — on false blocks.** A battery of N narrow checks is N independent block-gates; if each fires spuriously even 5% of the time, the chance of at least one false block per artifact is `1 − 0.95ᴺ` ≈ **54% at N=15**. So a checklet swarm that decomposes well but calibrates poorly trades a broad critic's variance for a near-certain spurious block — which is why calibration is not optional polish but the precondition for decomposition to pay off at all. Calibrate each checklet's reject threshold on a **held-out** split (never the set you report on), tune the *whole suite jointly* under a family-wise guarantee (Learn-then-Test treats each threshold as a hypothesis and controls FWER across the battery), and where certain defect classes matter disproportionately, calibrate **per-class (stratified)** rather than trusting the marginal bound — LTT/CRC guarantees are marginal, so all the error can legally land in one class.

### 6.4 Value-of-information acquisition (don't run every check)

The robust default policy is **myopic EVI with a conservative risk threshold.** With "do-nothing" Bayes loss `L₀(s) = min{λ·p(s), c_V}`, define for unused checklet `j`:

```
VoI_j(s) = L₀(s) − E_{z_j|s}[ min{λ·p(s,z_j), c_V} ] − c_j
```

Acquire `argmax_j VoI_j(s)/c_j` over feasible unused checks. **Waive iff `u(s) ≤ α`** *and the bound rests on checks that actually cleared* (§6.1); verify if no remaining check has positive value or budget is exhausted. This acquisition step **is the evidence-recovery move** (§5.6, §6.1): in the uncertain middle band the system defaults to neither waive nor expensive hard-verify — it spends the cheapest check that most reduces risk, which is the ReCoVERR loop expressed as a cost-aware policy. Composition patterns and their tradeoffs:

| Strategy | Wins when | Main risk |
|---|---|---|
| **Sequential cascade** | Large easy-case fraction (best *mean* cost) | Tail latency from deep branches |
| **Parallel bundle** | p95/p99 latency matters; cheap checks batch | Over-checking easy cases |
| **Hierarchical route** | Heterogeneous task families | Router error hides a useful specialist |
| **Conditional branch** | Strong early failure-mode signal | Harder auditing/guarantee accounting |

A good production design is a **hybrid**: one parallel front-end bundle, then sequential VoI refinements only for the ambiguous middle band. One quantitative gate governs whether a cheap-first cascade pays at all: **try-cheap-first beats always-verify only if the cheap tier's pass rate exceeds the cost ratio — `1 − f_L > c_L / c_H`** (cheap-tier escalation rate `f_L`, costs `c_L`, `c_H`). Below that line, misrouting penalties and escalation latency erase the savings — measure `f_L` before committing to the cascade.

### 6.5 Finite-sample guarantees — certify, don't hope

Population statements need finite-sample protection. Three complementary layers:

1. **Conformal risk control / RCPS** — distribution-free control of a monotone loss via a calibration split.
2. **Learn-Then-Test / Pareto Testing** — risk control as multiple-hypothesis testing over a threshold/policy family; Pareto Testing handles *simultaneous* constraints (e.g., `L_fw ≤ β` **and** `κ ≥ γ`, which automatically gives `R_fw ≤ β/γ`).
3. **Random auditing** — the operational certificate. Audit `m` waived items uniformly; with `r=0` misses, the one-sided Clopper–Pearson upper bound is `1 − δ^(1/m) ≈ −ln δ / m` — at 95%, the familiar **"rule of three" ≈ 3/m**:

| Target upper bound on `R_fw` (95%, 0 misses) | Audited waived items needed |
|---|---:|
| 5% | 59 |
| 2% | 149 |
| 1% | 299 |
| 0.5% | 598 |

**Keep a nonzero uniform random-audit stream forever** (it can't be gamed by the model and it detects drift). Run **two streams**: a *uniform* stream for exact certification and drift detection, and a *targeted* stream oversampling high-risk bins for fast learning. Only the uniform stream feeds simple binomial certificates; the targeted stream is used with importance weights or for model improvement only. Under covariate shift, switch to **weighted conformal** (estimate the test-to-calibration density ratio from unlabeled covariates) or temporarily lower `κ` until new calibration data accumulates.

**The guarantee changes *type* with oracle availability — this is the single most important qualification on the keystone.** Where a sound oracle exists (CQIEA-style retrieval/claim checks; deterministic system/continuity validators), R_fw is a **true-correctness** bound: conformal abstention controls `Pr[no-abstain AND error] ≤ α` directly (the controlled loss *is* the false-waiver rate), and ≤2–5% high-severity is realistic and achievable. Where no oracle exists (prose quality, open narrative judgment), **R_fw is not certifiable as a true-failure bound at all** — the best attainable guarantee is *bounded disagreement with a noisy human-severity proxy* (the "trust-or-escalate" construction: a provable **agreement** guarantee, e.g. ≥80% human agreement at ~80% coverage, not a correctness guarantee), and that proxy's own error sets a noise floor. **Do not report the two as the same number.** An oracle-poor pack's target must be reframed as "≤X% disagreement with human high-severity labels at Y% coverage, abstain-or-advisory fallback," and if the human raters' own inter-rater agreement is below the promised bound, the bound is unmeasurable — renegotiate it.

**The binding practical constraint is high-severity labels, and it is the program's critical path.** Certifying a small bound is sample-hungry: by the rule of three, ≤2% at 95% with zero observed failures needs ~150 high-severity items, and *more* (via a Clopper–Pearson interval) if any failure occurs — **per domain, per severity tier**. Acquire on the order of **150–400 labeled high-severity items per domain** before claiming a ≤2% bound; **report a one-sided upper confidence bound, not a point estimate** (an underpowered audit can appear to satisfy ≤2% by chance); set the **internal α strictly below the externally promised bound** as a drift margin; and **halt auto-waiver and widen escalation the moment realized R_fw on the rolling audit approaches the internal α.** Two reporting rules travel with this: precision and NPV are both **prevalence-dependent**, so a reject-precision measured on a defect-rich seeded set is optimistic for rarer production traffic — **report NPV alongside the base rate** and re-weight to the estimated production prevalence before trusting an operating point; and for a layered stack, prefer **pipeline-aware conformal (joint-coverage calibrated on the realized joint score)** over a Bonferroni union across stages. (Anchors: Geifman–El-Yaniv selective classification as the existence proof — 2% guaranteed error at 53–59% coverage; Conformal Abstention where the loss equals R_fw; Conformal Risk Control / Learn-Then-Test / RCPS for the threshold guarantee; Cascaded Selective Evaluation for the agreement-type guarantee; PASC for the pipeline-aware joint bound.)

---


### 6.6 The certification governor — path-specific authority to waive

An optimizing scheduler may propose `stop_accept`; it may not authorize unverified acceptance. The certification governor is an independent principal that turns a valid selective-risk statement into authority over one exact artifact.

#### Bundle identity and certification closure

The complete `ControlPolicyBundle` remains the global identity of the deployed control plane. A certificate, however, binds to a **`CertificationClosure`**: the minimal causal slice capable of affecting the waiver decision for the certified stratum.

```text
CertificationClosure:
 artifact_stratum
 reachable_scheduler_branches[]
 reachable_producers[]
 reachable_checklets_and_probers[]
 qualifying_verifiers[]
 applicable_prompts_tools_schemas[]
 repair_paths_capable_of_mutation[]
 terminal_decision_policy
 parent_policy_digests[]
 effective_policy_digest
 closure_digest
 completeness_proof
```

The closure must be derived mechanically from the executable graph and policy, not manually asserted. A change invalidates a certificate when it intersects the closure, changes a parent policy or applicability premise, changes the reference protocol, or makes the closure proof incomplete. An unrelated component outside the reachable causal slice does not automatically invalidate the certificate.

This reduces unnecessary recertification without weakening exact-object discipline. A global bundle change still invalidates every closure that depends on the changed element.

#### Governor decision

On a terminal acceptance proposal, the governor checks:

- exact terminal artifact and canonical digest;
- current effective-policy and certification-closure digests;
- artifact stratum and support population;
- required `CheckletObservation` states;
- qualifying verification state;
- certificate validity and invalidation watermark;
- shift, incident, lease, and always-verify status;
- absence of post-verification mutation;
- acceptance and completion coverage floors.

It returns exactly one registered decision:

```text
authorize_verified_accept
authorize_certified_waiver
override_to_hard_verify
override_to_human
override_to_fail_closed
```

A certificate is not a bag of approved actions. It authorizes the frozen terminal policy represented by its closure. Recombining pieces from several certified closures produces a new, uncertified policy.

Certificates expire or become unsupported on causal events, not merely age. Draft A never authorizes draft B unless a named, versioned, independently validated semantics-preserving transformation proves equivalence.

Offline certification, confirmatory holdout, and permanent production audit remain distinct data roles. The uniform audit stream monitors continued support; it does not retroactively manufacture an initial certificate. Underpowered high-risk strata remain always-verify.

The same closure discipline applies to high-authority memory-promotion certificates and federated-release authorization, with their own estimands and required invariants.

### 6.7 Sibling-spine mathematics — false promotion and unauthorized effect

The §1.1 spines get their working definitions here; keep them **separate** from `R_fw`.

**False promotion.** For memory candidate `m` with `B_m=1` iff `m` is invalid/malicious/stale/mis-scoped at production-use time and `P_m=1` iff promoted:

```
R_fp = Pr(B_m=1 | P_m=1) κ_p = Pr(P_m=1) L_fp = κ_p·R_fp = Pr(B_m=1, P_m=1)
```

**Stratify by authority (mandatory):** `R_fp^(a) = Pr(B_m=1 | P_m=1, A_m=a)` — a single average can conceal an unacceptable high-authority failure behind a mass of harmless low-authority promotions. Promotion is **not** `EV>0` alone. With `p_t(m) = Pr(V_m=1 | D_{1:t})` the posterior that `m` is currently valid and correctly scoped, `EV_promote(m) = p_t(m)·G_m − (1−p_t(m))·L_m − C_m` is *one* term inside a gate dominated by authority-specific constraints:

```
Promote(m) ⇔ authority-feasible ∧ provenance/scope/compatibility known
 ∧ U_δ(R_fp^(a)) ≤ α_a ∧ LCB(ΔQ_m) ≥ q_min,a ∧ p_t(m) ≥ θ_a ∧ EV_promote(m) > 0
```

Conservative support counts by provenance family, not derivative count: `S_ind(m) = Σ_{g∈𝒢_m} w_g·φ(D_g)` (INV-M4).

**Contamination reproduction number.** `R_c = E[active contaminated descendants or harmful promoted uses caused by one active contaminated memory]`; `R_c < 1` (subcritical) is a promotion gate, `≥ 1` is a stop condition (§7.6). It is a design/experiment metric — a function of retrieval frequency, consolidation, write rules, promotion probability, monitoring, and revocation — **not** a precisely known online constant.

**Unauthorized effect.** Per severity class `j`: `R_ue,j = Pr(E_unauthorized,j = 1)`, entering the hierarchy as a **chance constraint** `U_δ(R_ue,j) ≤ β_j` for `j ∈ J_critical` (§1.2). Rare-event statistics rarely certify a small `R_ue` from zero observations, so §4A rests containment on invariant testing + independent oracles + audit UCBs and **says so** rather than reporting a fabricated bound. Detection/recovery telemetry (`T_d`, `T_q`, `T_r`, `N_h`) belongs in the §8 contract; survival/hazard estimators belong in the supporting reports.

**What stays out of the normative core.** A constrained POMDP is a valid research framing of sequential memory/effect governance under latent validity, and severity-weighted residual-risk scores are fine for sensitivity analysis and dashboards — but neither is a required implementation abstraction. The core needs states, actions, authority constraints, risk bounds, evidence contracts, telemetry, and promotion/rollback rules; it does not need a POMDP solver or a single freely-compensating scalar (INV-G3).

---
## 7. Contracts, artifacts, and handoff loss

### 7.1 Analyze by artifacts, not agents

| Artifact | Purpose | Common failure |
|---|---|---|
| Task brief | Request, constraints, domain, success criteria | Ambiguity, missing constraints, wrong domain |
| Route decision | Which roles/checklets/gates to invoke | Over-decomposition, missed specialist |
| Plan + acceptance spec | Steps, acceptance criteria, test intent | Non-executable, omitted requirement |
| Architecture/structure spec | Interfaces, dependency map, world bible, asset graph, perf budget | Over-design, contradictions |
| Evidence pack | Sources, citations, retrieved docs, claim map | Unsupported claims, stale sources |
| Candidate artifact | Code / memo / story / asset pack / doc | Functional/factual/continuity failure |
| Verdict packet | Gate results, defect findings, judge scores, human review | False defects, judge bias |
| Revision diff | What changed and why | Regressions, oscillation, reward hacking |
| Release package | Accepted artifact + docs + provenance | Unsupported additions, doc drift |

### 7.2 Typed contracts

Every node validates its output against a schema before handoff. Validation that can affect authority runs under a distinct principal and a sufficient `IndependenceProfile`; “use another model” is not a substitute for the profile.

Generic producer contract:

```text
task_id
inputs[]
decision_rights[]
outputs[]
artifact_scope
integration_authority
requested_actions[]
authority_requirements[]
required_execution_capabilities[]
resource_requirements[]
sandbox_requirements
network_requirements
effect_classes[]
stopping_condition
escalation_rule
non_responsibilities[]
```

The contract requests actions and authority; it never carries credentials. The broker resolves actions against immutable `ActionContract` entries and issues grants out of band.

Generic checklet contract:

```text
checklet_id
criterion
input_scope
requiredness: mandatory|conditional|optional
selection_predicate
output_schema
allowed_observation_states[]
evidence_requirements
calibration_target
authority_request
required_independence_predicate
required_oracle_predicate
non_authority: cannot_mutate_candidate
```

Generic `CheckletObservation`:

```text
checklet_id
artifact_digest
scope
requiredness
state
selection_reason
findings[]
evidence_family_ids[]
independence_profile
oracle_profile
confidence_raw
confidence_calibrated
started_at
completed_at
failure_reason
```

A finding records `claim`, exact `locus`, falsifiable `trigger`, evidence level, severity, and reproducibility metadata. Missing required evidence produces `abstain` or `mechanically_invalid`, not a guessed verdict.

Generic adversarial prober contract:

```text
target
guardrails_and_invariants[]
technique
output: candidate_break{trigger, observed_failure, evidence_level}
required_oracle_predicate
non_authority: cannot_mutate_candidate
```

A confirmed executable break is an objective signal within the oracle's validated boundary. A claimed break remains refuted-by-default until independently reproduced.

### 7.3 Structured outputs are a reliability lever, not cosmetics

When a role emits prose where a typed schema was possible, the *next* gate gets weaker (a biomedical-extraction study found judges performed poorly until outputs were normalized into structure — ~15% accuracy gain from structure alone). This applies to plans, evidence packs, verdict packets, and docs alike.

But a schema only helps if it is *validated*. Schemas create **false certainty** when they permit junk placeholders or silently missing evidence — you get well-formatted nonsense that reads as authoritative. Pair every schema with required evidence-bearing fields, provenance/cross-field consistency checks, and an explicit `abstain` state when required evidence is absent. A schema without validation is worse than prose, because it launders an empty finding into a confident-looking one.

### 7.4 Requirement traceability — intent preservation as a graph

A flat fraction of “constraints retained” treats all requirements as equal and assumes one source requirement maps to one downstream field. Real work requires a traceability graph.

```text
RequirementTrace:
 requirement_id
 source_artifact_digest
 source_locus
 severity
 authority_class
 downstream_realizations[]
 derived_requirements[]
 state: preserved|refined|deferred|waived|contradicted|missing|unverifiable
 waiver_authority
 evidence_refs[]
```

A requirement may be split into several obligations, refined into a more precise contract, intentionally deferred, or waived by an authorized principal. Those are not equivalent to disappearance.

Report at least:

```text
weighted_handoff_loss
high_severity_loss
unauthorized_transformation_count
contradiction_count
unverifiable_count
waiver_count_by_authority
loss_by_graph_edge
loss_by_artifact_type
```

`weighted_handoff_loss` uses preregistered severity weights; it is never the only number. Any missing, contradicted, or unauthorized transformation of a non-waivable requirement is a hard failure regardless of the aggregate score.

Downstream artifacts cite the requirement IDs they realize. The graph controller invalidates only realizations causally dependent on a changed requirement or upstream artifact. This makes “the next agent understood it” an inspectable claim rather than a hope.

### 7.5 Cross-system handoff — the portable verifier-sufficient manifest

§7.4 governs handoff between *your* roles, which share your contracts, memory, and conventions. A different problem appears when a *finished* artifact crosses a **system boundary** to an agent from another system: that consumer shares *nothing* out-of-band — not your context, memory, model, or conventions — it sees only the artifact bytes and whatever canon you both reference. There is no back-channel, so the artifact must be **self-describing and verifier-sufficient** or the handoff fails silently (the foreign agent acts on an artifact it cannot actually check). Agent-to-agent work confirms the gap and measures its cost: opaque/prose handoff completes only a minority of tasks under drift, and schema/version mismatch is a primary failure axis.

**The backbone is proof-carrying code — architecture borrowed, soundness explicitly not.** PCC ships a checkable certificate with the artifact so an untrusted consumer verifies *without trusting the producer*, reducing its task "from proving to checking" against a public policy, with a minimal trusted computing base. Transfer the architecture wholesale — **a manifest travels with the artifact; the foreign verifier checks it independently against shared canon; trust nothing in the manifest** (refute-by-default — the §5.6 evidence rule applied to the interface). Do **not** transfer the soundness: PCC's check is a *decidable* proof over machine semantics; a natural-language artifact has no such proof, so the foreign verifier is an **oracle-ceiling-bound judge (§5.7)** and every reliability claim is *relative to that ceiling, never an absolute correctness guarantee*. Blurring this over-promises.

**The manifest** is a single canonicalized object (RFC 8785 / JCS for its own integrity hash) carrying falsifiable, content-addressed claims — structurally an assume-guarantee contract (consumed facts = assumptions; established facts + exit state = guarantees):

```
manifest_version
artifact_ref { content_hash, media_type }
intent_contract { intent, acceptance_criteria[]{id, predicate, kind} }
consumed_facts[] { fact_id, canon_hash, canon_rule, schema_version } # assumptions, by hash
established_facts[] { fact_id, canon_hash, canon_rule, derivation } # guarantees, falsifiable
exit_state { declared: complete|blocked|partial, exit_conditions[]{id, predicate, satisfied_claim} }
invariants[] { id, predicate, scope }
canonicalization { rule, version, value_profile, complexity_bound } # required only cross-canon
provenance { issuer, signature } # authenticity, NOT trust
```

The **foreign-verifier protocol** (manifest + shared canon only, no producer state): verify manifest integrity/signature (authenticity, not trust) → resolve each consumed-fact hash against local canon → check each established fact is derivable-from / consistent-with canon + consumed facts (*this step is the judge, not a proof*) → evaluate exit conditions → check invariants → accept iff all pass at the judge's threshold, else reject. Because each check is a separate, labeled step against a separate field, rejection is **attributable**: it keys to a named component — `CONSUMED_FACT_MISMATCH(Fᵢ)` (with a `DRIFT` vs. `DISAGREEMENT` sub-code), `UNMET_EXIT_CONDITION(Xₖ)`, or `VIOLATED_INVARIANT(Iₘ)` — turning an opaque "off" into an actionable defect report (the §4.6 backtrack-to-source, across systems). An "opaque off" is any rejection that can't be keyed to an id, and the *attribution-localization rate* is a first-class metric .

**The load-bearing decision is how a fact-claim is addressed, and it is forced by whether canon is shared.** Two regimes:
- *Floor — shared canon store:* both sides resolve the identical content address, so the manifest's only job is to carry true, sufficient claims. If a foreign verifier can't agree even here, the mechanism is dead — stop.
- *Ceiling — each system has its own canon, reconciled by hash:* a failure appears the floor can't see — **representational drift**, where the *same* fact serialized/normalized/versioned differently hashes differently. Addressing facts by **raw-serialization hash fails on any drift** (key order, whitespace, number format, schema version), making the handoff fail for reasons unrelated to artifact correctness — exactly what would make a foreign verifier *less* reliable than a same-system one.

**Decision: address fact-claims by a *canonicalized* form**, with a mandatory named+versioned `canon_rule`, a constrained `value_profile`, and a `complexity_bound`. The cost — both systems must implement the same canonicalization — is the irreducible price of statelessness. And canonicalization *shrinks but cannot eliminate* drift: the standards document residual gaps (JCS restricts numbers to IEEE-754 doubles → carry large/precise numbers as strings; graph canonicalization admits language-tag-case ambiguity that yields different hashes → lower-case them), and graph canonicalization is graph-isomorphism-hard, so an abort/`complexity_bound` is required against poison inputs. So the floor→ceiling reliability delta has an **irreducible floor strictly above zero** — and that delta is the number that says whether "cross-system" handoff is real or just same-system handoff in a costume. **Adopt standards rather than invent**, to keep the TCB small: RFC 8785 for manifest integrity, an in-toto-style Statement (subject-by-digest) for `artifact_ref` and the fact lists, the Verifiable-Credentials issuer/holder/verifier framing with DSSE/JWS for `provenance`. Which fields are *required* is itself empirical : the `canonicalization` block earns its place only without a shared store; the rest is hypothesized irreducible.

**Scope note .** §7.5 governs *completed-artifact* handoff : a foreign verifier inspecting bytes it did not produce. §7.7 governs *execution delegation* : a foreign executor producing the artifact without undeclared access to the origin. They are different problems and get different contracts — §7.7 references this manifest as its post-execution half but does not overload it. The manifest is deliberately described as verifier-sufficient, not self-verifying; §7.7 uses the same **`ExecutionEvidenceManifest`** / *verifier-sufficient* framing: a signature makes claims **refutable**, never **true**.

---


### 7.6 Governed cross-run memory and authority

Persisted information is a stateful policy surface and supply-chain artifact. Memory creation and memory authority are separate operations. Runtime evidence may be preserved broadly without becoming eligible to influence later work.

#### Lifecycle

The authoritative machine is `memory_record` in `state_machines.yaml`:

```text
evidence → candidate → verified_candidate → canary → promoted
```

with side or terminal states:

```text
needs_revalidation · quarantined · superseded · revoked · expired
```

Only `canary` and `promoted` are retrieval-eligible. `verified_candidate` means that evidence checks passed; it does not grant production authority.

Authority classes are:

```text
evidence · advisory · operational · protected
```

Protected canon, policy, permissions, and root trust have no automatic runtime write path.

#### Two attestations

Promotion requires:

- an `OutcomeAttestation` proving the source run's relevant outcome under its oracle;
- a `MemoryTransitionAttestation` evaluating whether the derived memory faithfully preserves evidence, preconditions, exceptions, scope, compatibility, and uncertainty.

Raw source evidence and derived memory remain separate immutable records. A failed derivation can be repaired without erasing the evidence that exposes it.

#### Retrieval

Eligibility precedes ranking:

```text
tenant/namespace
→ authority class
→ lifecycle
→ principal/domain/task/role scope
→ compatibility and validity epoch
→ supersession/contradiction
→ semantic relevance
```

Similarity may reorder eligible records. It may never restore an ineligible record.

#### Promotion and invalidation

Verification burden scales with authority, scope, retrieval frequency, reversibility, downstream action power, tenant exposure, descendant count, and consequence if wrong. Evidence support is counted by provenance family, not derivative count. Revocation and invalidation traverse descendants.

A promotion decision evaluates explicit predicates over the verifier's independence and oracle profiles; it does not compare a scalar independence rank.

```python
def decide_promotion(candidate, policy, evidence):
 if candidate.target_namespace == "protected":
 return require_authenticated_owner(candidate)
 if unknown_provenance(candidate):
 return quarantine("UNKNOWN_PROVENANCE")
 if unknown_scope_or_compatibility(candidate):
 return quarantine("UNKNOWN_COMPATIBILITY")
 if not outcome_attestation_passes(evidence):
 return reject("SOURCE_OUTCOME_NOT_VERIFIED")
 if not transition_attestation_passes(evidence):
 return reject("MEMORY_TRANSITION_NOT_VERIFIED")
 if evidence.false_promotion_ucb > policy.max_R_fp[candidate.authority_class]:
 return reject("PROMOTION_RISK_EXCEEDED")
 if not independence_predicate_passes(evidence.independence_profile, policy):
 return needs_revalidation("INSUFFICIENT_INDEPENDENCE")
 if not oracle_predicate_passes(evidence.oracle_profile, policy):
 return needs_revalidation("ORACLE_NOT_QUALIFIED")
 if canary_required(candidate, policy) and not evidence.canary_passed:
 return keep_candidate("CANARY_REQUIRED")
 return atomic_promote(candidate, policy, evidence)
```

Learned memory management remains advisory and shadow-only until it beats the transparent policy on held-out families. It never mints promotion authority.

### 7.7 Federated execution boundary — declared execution closure

Completed-artifact verification asks whether a foreign verifier can inspect bytes it did not produce; federated execution asks whether a foreign executor can produce those bytes without undeclared access to the origin. The mechanism is not "a remote agent with a manifest" — it is a **declared execution closure**: the complete set of task semantics, immutable or validity-bounded inputs, canon, runtime identities, tools, authority, budgets, recovery semantics, effects, acceptance rules, and trust policy permitted to influence a remote execution. The distinction that makes this precise: a remote content store is **declared infrastructure** when every read is authorized, versioned/immutable, content-addressed, and in the trace; **hidden state** is anything that can influence execution without appearing in the declared closure. The claim is bounded and system-relative — remote execution can be *noninferior* to local on task outcomes while preserving specified safety, effect, provenance, disclosure, and verification properties within preregistered margins — and the non-claims are load-bearing: **not** byte reproducibility, identical traces, semantic proof from a signature, executor truthfulness, universal cross-domain equivalence, or exactly-once effects.

**Split the manifest.** §7.5's object mixes what was known before execution with what was learned during it. the architecture separates four typed objects: **`ExecutionContract`** (immutable pre-execution input + authority envelope), **`ExecutionEvidenceManifest`** (realized derivation, effects, checks, attempts, disclosure, attestation), **`ForeignVerificationDecision`** (independent verifier output), **`ReleaseDecision`** (final disposition after release-time validity recheck). This is what makes fault attribution clean.

**Six non-compensable invariants (INV-F1…F6).** (1) *Artifact integrity* — every accepted subject matches its recorded digest + canonical form. (2) *Declared closure* — no accepted result depends on an undeclared input, model, canon epoch, plugin implementation, tool, policy, cache, credential, or service. (3) *At-most-one authoritative logical effect* — for a stable logical-effect key, committed authoritative effects ≤ 1 (this is INV-A5 at the federation boundary). (4) *No stale release* — every policy-relevant dependency is valid at the serialized release decision. (5) *Verifier isolation* — the foreign verifier uses only the portable package, declared trust roots, sealed evaluator services, and a fresh sandbox; it is **not** a producer-side self-critique. (6) *No unauthorized disclosure* — prohibited fields, raw secrets, canaries, or undeclared sensitive spans never cross the boundary or appear in artifacts, manifests, traces, or verifier packages. These are constraints (§1.4), not quality dimensions.

**Logical-effect identity + reconciliation.** Distinguish `command_id · message_id · attempt_id · artifact_id · logical_effect_id · physical_delivery_id · commit_id · checkpoint_id · release_id`. A duplicated message is not a duplicated intent; a new message id can repeat the same business effect; repeated physical execution is safe when only one authoritative commit occurs. The guarantee is **at-most-one authoritative commit per stable logical-effect identity, or an explicit `reconciliation_required` state** — never universal exactly-once. A compensation is a *new* logical effect; it does not erase that a duplicate occurred.

**Release-time closure revalidation.** Content hashes reproduce what was *used*; they do not prove it is still *valid*. Distinguish `execution_epoch · artifact_acceptance_epoch · release_epoch · valid_until · supersedes · revokes · requires_latest`. A result can be perfectly reproduced and still be stale, so canon drift needs both provenance and validity semantics, checked atomically at release by the §7.7 release controller (a broker-owned effect adapter, §4A).

**Permitted vs. prohibited status claims.** The package may assert `integrity_verified · provenance_verified · declared_closure_verified · machine_acceptance_reproduced · effect_state_reconciled · release_validity_verified`. It may **never** infer `semantically_true · globally_correct · malicious_executor_excluded` from a producer signature — "self-verifying" is retired precisely because it invites that inference. Transport is neutral: A2A, MCP, HTTP, queues, and durable-workflow engines can all carry this; "A2A vs MCP" is the wrong experiment. "Full trace" means all externally causal events (declared inputs, context objects, prompt hashes as policy permits, model/tool identities, tool I/O, artifact edges, decisions, effects, checkpoints, verifier results) — **not** hidden token-level reasoning, which stays out for privacy, storage, and security reasons.

```yaml
ExecutionContract: # pre-execution; immutable; the closure the remote MAY use
 contract_schema: {uri, version, digest}
 execution_identity: {executor_spec_digest, model:{provider, resolved_id, allowed_substitutions[]},
 policy_digest, tool_implementations[], runtime_digest}
 input_closure: {objects[], canon_epochs[], validity_policy, missing_or_unknown[]}
 authority: {permissions[], effect_classes[], network_allowlist[], secret_handles[]} # handles, never raw secrets
 delivery: {command_id, logical_intent_id, retry_policy, checkpoint_policy, cancellation_policy}
 acceptance: {verifier_profile_id, required_gates[], nonwaivable_rules[], waiver_policy}

ExecutionEvidenceManifest: # post-execution; what actually happened (refutable, not proof)
 schema_version; contract_digest
 subjects: [{artifact_id, media_type, canonicalization_profile, digest, length}]
 realized_dependencies[]; actual_executor_identity; substitutions[]; external_reads[]
 attempts: {invocation_id, attempt_ids[], checkpoints[], restart_lineage[]}
 effects: [{logical_effect_id, parameter_digest, attempt_ids[], dispatch_state,
 acknowledgement_state, commit_state, reconciliation_state, authoritative_ledger_ref}]
 disclosure: {fields[], bytes, tokens, recipients[], purpose_tags[], sensitive_classes[], secret_handle_uses[]}
 attestation: {issuer, envelope_type, signature_ref, trust_profile_id}

ForeignVerifierProfile: # INV-F5: isolation is a declared property
 verifier_id; trust_roots[]; allowed_evaluator_services[]; sandbox_identity; sealed_checks[]
 acceptance_policy; canonicalization_support[]; independence_profile_relative_to_executor; reruns_executable_tests: bool
 observes_effect_and_disclosure_ledgers_independently: bool
```

**Rejection is attributable** — every foreign-verifier rejection keys to a named object: `CONTRACT_DIALECT_UNSUPPORTED · DECLARED_CLOSURE_INCOMPLETE · UNDECLARED_DEPENDENCY · EXECUTOR_IDENTITY_MISMATCH · PLUGIN_IMPLEMENTATION_MISMATCH · CANON_EPOCH_MISMATCH · STALE_AT_RELEASE · EFFECT_DUPLICATE · EFFECT_AMBIGUOUS · ATTESTATION_INVALID · VERIFIER_TRUST_FAILURE · DISCLOSURE_POLICY_VIOLATION`. Legitimate non-failure terminal states: `quarantine`, `reconciliation_required`.

---
## 8. Telemetry and observability

Traces describe causal structure; authenticated JSONL events provide the immutable record. Every runtime event validates against `schemas/telemetry_event.schema.json` before append. Unknown top-level fields are rejected; domain-specific fields live under `extensions`.

Required envelope groups:

```text
schema_version · event_id · event_type · occurred_at
trace{trace_id, span_id, parent_span_id, linked_span_ids[]}
run{run_uid, task_id, stage, artifact_id, artifact_digest}
producer_principal{principal_id, authenticated, authentication_ref}
decision{action, reason_codes[], confidence, terminal_state}
metrics{latency_ms, prompt_tokens, completion_tokens, tool_calls, tool_successes, cost_usd}
authority{monitor, transition_id, policy_bundle_hash, effective_policy_digest, closure_digest,
 invalidation_watermark, grant_digest, certificate_id, governor_decision, broker_decision_code,
 approval_class, effect_slot_id, operation_id, operation_state, mechanically_valid,
 approval_created, ledger_checkpoint, witness_refs[]}
verification{checklet_observation, independence_profile, oracle_profile}
failure · extensions{}
```

The exact closed schema is `schemas/telemetry_event.schema.json`; `examples/event.valid.json` is a validator-clean instance.

The schema establishes structure. `core_lint.py` then performs registry and cross-field validation:

- the runtime manifest must verify before any event, transition, or pack validation;
- nested code and state values must exist in pinned registries;
- an unauthenticated producer cannot append production evidence;
- mechanical invalidity cannot create an approval;
- waiver requires a valid certified-waiver governor decision and certificate;
- `outcome_unknown` cannot terminate as accepted or waived;
- monitor decisions require current policy, closure, transition, and invalidation bindings;

A valid schema with invalid cross-field semantics is rejected. `{}` is not an event. Unknown enum values do not degrade to warnings.

Core operational views cover quality, acceptance/completion coverage, false-waiver and verified-path error, routing, requirement traceability, revision, cost, judge bias, checklet missingness, authority transitions, effect reconciliation, certificate support, memory promotion, invalidation latency, and producer-authentication failures.

Evidence surfaces never substitute for veto surfaces. Dashboards consume the governed event stream; they do not decide whether the system is healthy.

## 8A. Runtime — faults, resources, trust boundaries, and human workflow

Models, tools, networks, humans, and the runtime itself fail. Expected faults include timeouts, malformed output, schema-valid nonsense, retrieval failure, verifier disagreement, rate limits, budget exhaustion, stale dependencies, prompt injection, sandbox violations, ambiguous non-idempotent effects, lease loss, ledger lag, and policy conflicts.

Default handling:

- validate structure and evidence semantics before downstream use;
- retry only idempotent or explicitly reconciled operations;
- persist accepted state after every node;
- resume from the last valid artifact and current policy snapshot;
- fail closed on non-waivable gates;
- return best-validated partial output only when policy permits;
- never convert an unknown outcome into zero findings or success.

### Resource governor

The resource governor controls cost, latency, tokens, tool calls, and revision rounds. It has no waiver authority. It reserves mandatory verification and recovery budget before spending on candidate expansion. Budget exhaustion routes to an explicit terminal disposition, never an undefined partial state.

### Trust model

**Untrusted:** models, user and retrieved content, tool responses, plugin code and metadata, generated parameters, producers and verifiers under test.

**Trusted computing base:** broker, policy and identity authority, root keys, resource resolver, sandbox enforcement, broker-owned effect adapters, authority ledger, invalidation bus, and independent oracles—subject to the stated compromise assumptions and witnessing controls.

**Residual:** kernel and hardware compromise, covert channels, simultaneous compromise of broker and evaluator, incorrectly authored policy, and semantic truth beyond the declared oracle boundary.

Authenticated code is not necessarily benign. Containerization is not by itself a sandbox profile. A mechanically invalid call never becomes a human-approval prompt.

### Human workflow

Human review is an asynchronous queue with a reason code, exact artifact snapshot, evidence packet, requested authority, SLA class, and label schema. It blocks only affected nodes where safe. Human decisions record whether the person acted as expert adjudicator, protected owner, or both; those roles are not conflated.

### Run and lease identity

Runtime status is governed state:

1. Status snapshots are complete and atomically replaced, never field-merged across runs.
2. Every projection reconciles displayed `run_uid` with the current lease holder; mismatch renders stale/unknown.
3. Liveness signals are not identity.
4. Lease renewal has a production caller; one live lease exists per scope.
5. Stop and freeze are monitor-enforced authority boundaries.
6. Terminal reasons remain distinct and come from the closed registry, including `lease_lost`.

### Ledger and invalidation availability

A monitor may not authorize from stale authority state. Each decision records:

```text
ledger_checkpoint
bus_partition
bus_watermark
witness_refs[]
freshness_deadline
```

If the ledger, bus, or witnesses disagree or cannot establish freshness, the transition routes to reconciliation or fail-closed. Operational availability never justifies using an unwitnessed old snapshot for a consequential commit.

## 9. The convergence / stopping controller

Self-refinement does **not** monotonically improve (Self-Refine ~20% avg gain across 7 tasks, but gains concentrate in rounds 1–2; intrinsic self-correction *degrades* reasoning without external feedback). An explicit stopping rule is mandatory.

**Dual-axis metrics.** *Outcome:* deterministic pass-rate + per-dimension win-rate (Wilson CIs) + BT rating + PPI-corrected win-rate. *Process/convergence:* per-iteration score trajectory; **marginal-gain decay** (stop when Δ < ω × first-step gain); successive-draft semantic distance (shrinking = converging; not = oscillating; growing = diverging); late score variance; **Goodhart/reward-hacking divergence** (proxy judge score rising while held-out signal or deterministic pass-rate stalls/falls).

**Stop when** any of: (a) marginal gain < δ for two consecutive rounds (plateau, e.g., Δ < 0.02); (b) max-iteration budget reached; (c) regression vs. best-so-far; (d) reward-hacking divergence triggers; (e) successive-draft diversity collapses. **Always select the best *validated* iteration on a held-out signal, not the last** — and give the critic/checklets veto only when reject precision is calibrated ≥ 0.90.

**Governed-transition stop rules.** `stop_accept` is a *proposal*; only the §6.6 governor produces terminal verified/waived acceptance. Beyond the convergence rules above, the run halts or fails closed on: `outcome_unknown` from a provider → no blind retry (§4A); effect slot exhausted → no new operation; grant expired/revoked or certificate unsupported → replan within current authority or fail closed; repeated mechanical failure → bounded replan, **never** elevate; sandbox violation → terminate the action and quarantine the plugin version; memory `R_c ≥ 1` after mitigation or descendant revocation unreliable → freeze promotion and revert down the §7.6 ladder; federated `closure_incomplete`, `effect_ambiguous` past budget, `stale_at_release`, `attestation_invalid`, `foreign_verification_failed`, or `disclosure_violation` → quarantine or fail closed (§7.7). `quarantine` and `reconciliation_required` are legitimate non-failure terminal states, not exceptions. "No more actions were taken" is still never a valid stop reason.

---

## 10. Evaluation — benchmark, splits, ablation, promotion

### 10.1 Splits & labels

Six splits have distinct purposes because certification, confirmation, and monitoring are different statistical jobs: **Development** (iterate prompts/contracts), **Policy-development** (design scheduler/router/memory/promotion policies), **Certification-calibration** (locked protocol; issues `R_fw`/`R_fp` certificates over frozen bundles — never reused to design the policy it certifies, §6.6), **Regression** (frozen; historical failures mined by MAST mode; must never degrade), **Confirmatory holdout** (private/paraphrase-perturbed; touched only for promotion), and the permanent **production random audit** (§6.5; monitors continued validity or feeds an explicitly sequential certificate — it does not by itself mint the initial bound). A single split doing certification *and* confirmation *and* monitoring is how an underpowered audit launders itself into a promotion-grade claim. Label **both** final-output *and* intermediate-process dimensions (per-handoff: was intent preserved? per-stage: which failure mode?). Use ≥2–3 annotators on a subset, report **Cohen's κ / Krippendorff's α**, *preserve disagreement* rather than forcing false gold, and version dataset + rubrics + judge prompts together with immutable holdout hashes.

### 10.2 The flawed-artifact tests are essential

Hand the loop a flawed plan, a buggy implementation, a fabricated citation, a broken asset reference. These isolate whether downstream roles *catch upstream defects* rather than producing plausible new prose. They are the only way to measure the verification stack honestly.

### 10.3 Ablation matrix (the core scientific step)

Compare on identical task instances under a **fair harness contract** (same base models, equalized token/runtime budgets, identical tools/context/stop-policies/evaluator suite — it is trivially easy to confuse "extra compute" or "a friendlier evaluation adapter" with architectural improvement):

1. **Strong single agent, same tools+context** (null hypothesis).
2. Current full loop.
3. Reduced configs — leave-one-out + merges (orchestrator↔planner, planner↔architect, critic→checklets, documentor inline).
4. **Dynamic specialist-on-demand routing.**
5. Loop-order/parallelism/revision variants (research-before-plan vs. after; serial vs. parallel; 0/1/2 revision rounds).

**Statistics (where most agent evals fail):** single-run pass@1 varies **2.2–6.0pp** depending on which run you pick (SD > 1.5pp even at temperature 0) — *reported 2–3pp gains can be pure noise.* Use **T ≥ 5 runs/task**; task-level bootstrap CIs (≥10k resamples) and Wilson intervals at small n; **McNemar / paired bootstrap** for dependent samples; **Holm–Bonferroni** for multiple comparisons; power-analyze the eval-set size to detect your expected effect above the noise floor. Be concrete about that last point: detecting an absolute quality difference of **δ = 0.03 at 80% power takes on the order of ~1,000 independent items** — so a 15- or 30-question set can detect only *large* effects and is badly underpowered for a parity/non-inferiority claim. Two consequences: **paired-difference testing (same items across arms) is the single highest-leverage move** (it exploits cross-arm correlation to cut variance), and a result on a tiny set is a **pilot / go-no-go signal, not a promotion-grade claim** — expand to ≥150–200 stratified items before any parity conclusion. Where a routing or selection decision is involved, also compute the **oracle ceiling** (perfect routing/selection) so the gap attributable to *decision error* is separated from the gap attributable to *route/candidate quality*.

### 10.4 Cross-domain benchmark suite + synthetic simulation

Mix settings where the hard verifier is exact, approximate, and human-backed: MMLU/BBH (reasoning breadth), GSM8K/MATH (multi-step, checkable), DROP (discrete reasoning), HumanEval/SWE-bench-Verified/LiveCodeBench (execution; contamination-resistant), TruthfulQA/HaluEval (factuality), HELM/WildBench (real-user, multi-metric). For the *verifier itself*, add judge/verifier-specific benchmarks: **JudgeBench** (the sobering anchor — strong judges near-random on hard objective-correctness pairs), **CodeJudgeBench** (order-sensitivity in code judges), **PRM800K/ProcessBench** (step-level process verification), and **FActScore/FEVER/SimpleQA** (claim-level factual verification with abstention). And split the calibration data **temporally** — calibrate on one window, validate on a *later-in-time* window — so drift surfaces before deployment, not after. **Synthetic simulation** is indispensable for sweeping the *causal drivers* of false-waiver behavior that real benchmarks can't isolate — latent difficulty, **correlated checklet errors** (shared latent random effect), producer diversity, verifier imperfection `ε_V`, and shift severity. Sweep producer base error `π` (0.02–0.30), checklet hit `a` (0.55–0.95) and false-alarm `b` (0.01–0.30), pairwise correlation `ρ` (0–0.70), #checklets (2–20), `c_j/c_V` (0.005–0.10), audit rate `q` (0.5–10%), `α` (0.5/1/2/5%), shift (density-ratio 1–5).

### 10.5 Promotion gates

A change is eligible for promotion only when all applicable higher-order gates pass:

| Dimension | Required evidence |
|---|---|
| Objective validity | Every applicable deterministic, static, executable, source, and contract gate passes on regression and confirmatory holdout. |
| Artifact safety | Certified waiver strata meet their bound; verified-path residual error is separately bounded; `L_escape` and `R_accept` remain within policy. |
| Coverage | Acceptance and completion coverage meet preregistered floors; safety cannot be purchased by refusing everything. |
| Authority and effects | No invariant violation, unauthorized effect, stale authority state, unresolved policy conflict, or unreconciled consequential outcome. |
| Final quality | Noninferior to the strongest matched baseline on preregistered primary and severe-defect metrics. |
| Added machinery | Each added agent, checklet, route, model, or orchestration layer improves a qualified frontier dimension at matched metered budget. |
| Verifier authority | Auto-block or waiver authority applies only to calibrated slices satisfying the required independence and oracle predicates. |
| Regression | No material regression outside the preregistered noise tolerance; no failure class rises beyond its policy limit. |
| Economics | Total lifecycle cost—including governance, recertification, sandboxes, human review, and reconciliation—fits the declared budget after every higher tier passes. |

Threshold values are deployment policy, not architecture. They live outside this normative document, are calibrated on the actual workload, and are bound into the effective policy and certification closure.

## 11. The ML consistency layer

Machine learning does not replace hard verification or mint authority. It predicts where verification, routing, escalation, and revision budget are most valuable.

Build in this order:

1. log authenticated traces, artifacts, gates, human labels, escaped defects, costs, and terminal outcomes;
2. train the risk model for `Pr(reference protocol rejects | current evidence)`;
3. train route and checklet-value recommenders;
4. train requirement-trace and handoff-risk detectors;
5. calibrate model judges against expert labels;
6. predict revision gain and stopping value;
7. detect drift and anomalies; route uncertain cases to humans.

Useful prompt-based checklets may later become trained classifiers when labels justify it. The aggregator learns which evidence combinations predict low residual risk; it does not treat any one model as an oracle.

Every learned policy obeys four rules:

- it proposes; an Authorization Monitor authorizes;
- it runs in shadow until it beats a transparent baseline on held-out task families;
- its generated policy must carry a valid non-expansion proof under §1.5;
- drift, missing identity, unsupported scope, or stale closure forces the fixed fallback.

Learned models may recommend memory promotion, routing, evidence acquisition, closure checks, or reconciliation effort. They may not issue grants, certificates, promotions, releases, protected-policy changes, or stronger independence claims.

## 12. The domain-pack interface

A pack declares a required base profile and only the optional capability profiles it implements. The authoritative schema is `schemas/domain_pack.schema.json`.

```yaml
DomainPack:
 spec_version: "1.9"
 pack_id: example.coding
 pack_version: "1.0.0"
 profiles_enabled:
 - base_artifact
 - oracle
 - isolated_compute
 - effectful_execution
 - certified_waiver
 - publication

 base:
 artifact_types: []
 schemas: []
 known_failure_modes: []
 checklet_catalog: []
 telemetry_extensions: []
 safe_fallback_composition: {}
 canon_substrate: {}
 handoff:
 failing_reproduction_first: true
 production_file_budget: 12
 net_loc_ceiling: 800
 integration_authority:
 mode: single_per_scope
 scope_definition: repository_change
 parallel_patch_proposals: bounded_non_overlapping
 supersession_deletes: true
 self_authored_success_evidence: forbidden

 oracle: # required only with profile: oracle
 deterministic_checks: []
 static_analyzers: []
 executables: []
 source_rules: []
 rubric_dimensions: []
 human_review_triggers: []
 oracle_profiles: []
 qualifying_evidence_rules: []

 isolated_compute: # required only with profile: isolated_compute
 sandbox_profiles: []
 declared_input_types: []
 export_validators: []
 network_read_adapters: []
 resource_limits: {}

 effects: # required only with profile: effectful_execution
 action_catalog: []
 resource_types: []
 effect_classes: []
 principal_roles: []
 role_action_matrix: {}
 sandbox_requirements: []
 network_service_identities: []
 broker_owned_effects: []
 effect_slot_policies: []
 reconciliation_adapters: []
 hard_denied_surfaces: []
 legitimate_elevation_points: []

 memory: # required only with profile: memory
 memory_types_allowed: []
 memory_authority_ceiling: advisory
 memory_scope_dimensions: []
 memory_invalidation_events: []
 protected_namespaces: []
 causal_use_oracle: {}

 waiver: # required only with profile: certified_waiver
 risk_strata: []
 always_verify_rules: []
 qualifying_verification: []
 reference_adjudication_protocol: {}
 acceptance_and_completion_floors: {}
 certification_closure_rules: {}

 federation: # required only with profile: federated_execution
 portable_contract_profiles: []
 equivalence_margins: {}
 effect_policy: {}
 disclosure_policy: {}
 foreign_verifier_profiles: []
 containment_attack_cases: []
 remote_execution_admissible: {}

 publication: # required only with profile: publication
 publication_targets: []
 release_revalidation_policy: {}
 disclosure_checks: []
 rollback_or_retraction_actions: []
```

### Profile rules

- `base_artifact` is always required.
- Enabling a profile makes its object and profile-specific fields mandatory.
- Omitting a profile means the corresponding capability is unavailable, not empty-but-implicitly-enabled.
- Pack policy composes through §1.5 and may only narrow the effective policy.
- An oracle profile sets authority only for its validated slices.
- Open-ended code execution is declared through `isolated_compute`, never by placing a raw shell in `action_catalog`.
- Parallel workers may propose changes, but the base handoff profile identifies one integration authority per artifact scope and revision transaction.
- Experimental treatments and operating hypotheses are not pack fields.

This structure preserves a thin local pack while allowing production-grade capabilities where they are actually needed.

## 13. Build order and registry discipline

Build in dependency order:

1. authenticated telemetry, exact run identity, and a strong single-executor baseline;
2. typed artifacts, requirement traces, and schema validation;
3. deterministic fail-closed gates and the gate-runner;
4. protected control-plane namespace, identity authority, ledger, invalidation bus, and policy composition;
5. typed broker actions, isolated compute cells, resource handles, and independent effect observation;
6. grants, sandboxes, effect slots, operation reconciliation, and principal separation;
7. grounded checklets, typed observation states, adversarial probing, and evidence fusion;
8. certification closures, governor, uniform audits, and narrow waiver regions;
9. memory lifecycle and protected-canon firewall;
10. federated closure and release-time revalidation;
11. learned routing, scheduling, and promotion only in shadow;
12. domain packs and publication integrations.

Veto surfaces precede evidence surfaces. The first product milestone is one real slice, one consumer-observed wiring proof, one external boundary canary, and zero autonomous consequential release until the enforcement path works.

### Registry package

The normative runtime registry set is:

```text
invariants.yaml
codes.yaml
state_machines.yaml
policy_composition.yaml
verification_profiles.yaml
registry_governance.yaml
schemas/telemetry_event.schema.json
schemas/domain_pack.schema.json
schemas/checklet_observation.schema.json
registry.manifest.yaml
```

Machine-enforced values live in these pinned artifacts. Human-readable arguments remain in this document. The core does not duplicate complete enums or state machines in prose.

`registry.manifest.yaml` pins every runtime artifact digest. Its digest participates in `ControlPolicyBundle` identity. `registry_governance.yaml` defines protected edit authority for every registry family. Registry changes therefore require authenticated protected-tier review and invalidate affected certification closures through the bus.

Validation commands:

```bash
python core_lint.py verify-manifest
python core_lint.py check-event examples/event.valid.json
python core_lint.py check-transition task_node passed stale
python core_lint.py validate-domain-pack examples/domain_pack.valid.yaml
python -m pytest -q
```

Any registry mismatch, unknown code, unknown state, unlisted transition, invalid policy composition, malformed event, or profile-incomplete domain pack fails closed.

### Platform conformance

The core defines abstract sandbox, identity, broker, ledger, and observation requirements. Platform adapters declare the concrete controls implementing them and emit coverage attestations. A required control the platform cannot realize makes the capability unavailable. “Runs in a container” and “uses another model” are never accepted as complete conformance claims.

---

*End of normative Reusable Core v1.9.*

