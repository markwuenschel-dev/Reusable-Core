> **Reusable Core v1.10 — Volume IV: Research program and experimental contract**
>
> NON-normative. Grants no authority. Research questions, priors, treatment ladders, injection batteries, field evidence (E1), and open tensions. Formerly *Research Program v1.9* (RQ17/RQ18/RQ26 integrated, LaTeX-fixed).
>
> **Precedence:** the [v1.10 kernel](../reusable-core-v1.10-kernel.md) wins any conflict with this document. Internal references to "v1.9" and to sibling documents by their former names are historical; see the [supersession map](../README.md#supersession-map).
>
> **Fidelity:** everything below the end-of-header marker is the source document reproduced byte-for-byte (`Reusable_Core_Research_Program_v1_9_RQ17_RQ18_RQ26_integrated_math_latex_fixed.md`, SHA-256 `a4c70a045a53cc89`).

<!-- v1.10 volume header end -->
# The Reusable Core — Research Program & Experimental Contract
### Optional operator document for Reusable Core v1.9

> **Load boundary.** This is an optional operator/research document. It is not part of the runtime load set and grants no authority. It holds research questions, priors, treatment ladders, injection batteries, measurement contracts, field evidence, and unresolved empirical tensions. The normative core holds only architecture and operational contracts.
>
> **Canonical mechanisms already folded into the normative core:** RQ11 → spec §7.6 + §6.7 (memory lifecycle, `R_fp`, firewall) · RQ12 → §4A (broker, grants, effect slots) · RQ13 → §6.6 (scheduler/governor split, certificates) · RQ14 → §7.7 (declared execution closure) · RQ17 → implementation profile §10.10–§10.11 + §13.8 + §18.11–§18.12 (pack composition manifest, interaction gate, minimum certification scope) · RQ18 → certification durability / exact-context invalidation / successor-certificate semantics (canonical implementation §§5, 10, 13, 14, 18–19) · RQ26 → §0 + §8 + §10.5 + §11 (recursive evidence ≠ independent evidence, external grounding, routing support, adaptive-promotion evidence) · RQ8's competence/authority vocabulary → §1.3/§4A · RQ10's effect/replay semantics → §4A/§7.7 · RQ5's decision rule → §4.5 · RQ3's calibration condition → §6.3 · RQ6's mechanism → §7.5. What remains below for those RQs is the **experiment**, not the architecture.

>
> **Bindings.** Treatment identity is governed by `research/treatments.yaml`; operating proposals are in `research/thresholds.defaults.yaml`. Promotion still flows through the normative core's §10.5 gates and §5.7 independence/oracle predicates. A failed experiment is a simplification result.

---

## Answer ledger

**Answer ledger.** *Folded* means the mechanism is canonical in the normative core. *Open* means the empirical claim still awaits its preregistered experiment here.

| RQ | Question | Folded into | Still open (the experiment) |
|---|---|---|---|
| 1 | Does a dynamically routed loop beat B0 and the fixed loop at equal budget? | loop + routing §4.3, §4.6 | routed-vs-B0 on this workload |
| 2 | Do calibrated checklets + risk cut verifier/human volume under the `R_fw` bound? | machinery §6.1–§6.5 | volume cut + bound holding, per stratum |
| 3 | Do narrow checklets beat one broad critic? | the sharp condition §6.3 (uncalibrated decomposition is *worse*) | magnitude at equal cost |
| 4 | Does the task-graph controller beat a linear chain? | controller §4.6 | the head-to-head (no literature answer exists) |
| 5 | Best-of-N + selection vs. single-candidate + revision? | decision rule §4.5 (flips on verifier soundness) | the flip point on these verifiers |
| 6 | Can a foreign verifier decide from the manifest alone? | mechanism §7.5 | Δκ(floor→ceiling) protocol |
| 7 | Are results runtime-substrate independent? | — | equivalence across pinned runtimes |
| 8 | Capability routing vs. role routing? | competence/authority vocabulary §1.3, §4A | routing-accuracy + frontier wins |
| 9 | When do swarms earn their keep? | admission rule: beat `FAB-F0` at matched metered budget | the conditions, if any |
| 10 | Durable execution under faults? | effect/replay + recovery semantics §4A, §7.7 | fault-conditioned recovery comparison |
| 11 | Which memory write/promotion policy? | lifecycle + firewall §7.6, `R_fp` §6.7 (firewall non-negotiable at every rung) | `MEM-M4` vs. `MEM-M3` at matched verifier strength |
| 12 | Can a broker contain effects affordably? | broker + grants + slots §4A | `AUTH-T4/T5` containment magnitude + engineering cost |
| 13 | Joint scheduling under a certified waiver bound? | scheduler/governor split + certificates §6.6 | `SCHED-T5` headroom; certification economics |
| 14 | Remote ≡ local without hidden state? | declared execution closure §7.7 | `FED-X4` noninferiority — coding first, writing second |
| 15 | Can spec-instantiation be certified — wiring proofs + non-hermetic oracles at a cost that beats the audit flywheel they replace? | instantiation proofs §5.8; INV-G6/G7/G8; build rule §13 | the certification-cost question (possibly engineering, not research) |
| 17 | When do independently validated spines/domain packs compose with maximum modular reuse, and what is the minimum additional certification scope when they do not? | implementation profile §10.10–§10.11, §13.8, §18.11–§18.12 | linter conservatism/recall, evidence-dependence treatment, higher-order interaction prevalence, theorem coverage, certification-cost savings |
| 18 | How durable are certificates under model/prompt/tool/schema/policy/distribution/reference/dependency change, and how can Core recertify only what changed without stale authority? | exact-context CCH, successor-certificate semantics, closure-aware evidence preservation, fail-closed hidden-drift posture | semantic-impact precision; interaction closure; certified change envelopes; hidden-drift power; minimum-evidence recertification economics |
| 26 | When does repeated trace→selection→training→evaluation→deployment improve externally grounded capability rather than produce feedback monoculture? | recursive evidence provenance §0/§11; adaptive-learning telemetry §8; promotion evidence §10.5; split isolation + audit §10.1 | stability boundary; minimum effective exogenous information; causal diversity; early-warning measures; optimal intervention policy |

---

## RQ1–RQ5 — composition, verification, checklets, orchestration, producer strategy (was the answer ledger)

The architecture is a hypothesis until it wins under the fixed contract above. Five questions structure the first program; each is a falsifiable claim with a directional prior — and the prior status below reflects a literature pass, but *confirmed-in-the-literature is not confirmed-on-your-workload*: your own risk-coverage curve and holdout are the only authoritative answers.

- **RQ1 — Dynamic composition.** Does a dynamically-routed loop match/beat the strong single agent *and* the fixed full loop while cutting cost/latency under equalized budgets? (Prior: ≥20% cost cut at parity — **well-supported, often conservative** in routing/cascade studies; **caveat: the fixed full loop B2 is likely the *weakest* arm — single agents match or beat fixed multi-agent loops at matched token budget — so the real bar is a well-tuned B0, not B2.**)
- **RQ2 — Selective verification.** Do calibrated checklets + risk aggregator cut hard-verifier/human volume while holding `R_fw` under the preset bound? (Prior: 40–60% volume cut **— supported, conservative**; high-severity `R_fw` ≤ 2–5% **achievable as a true bound only where a sound oracle exists; in oracle-poor domains it is an agreement bound, not a correctness bound — §6.5**.)
- **RQ3 — Specialized checklets.** Do narrow checklets localize more actionable defects than a broad critic at equal/lower cost, without more false blocks — *only when structured and calibrated*? (Prior **confirmed with a sharp condition: decomposition *without* calibration is *worse* than one broad critic on false blocks — §6.3**.)
- **RQ4 — Plan orchestration.** Does the task-graph controller (§4.6) cut handoff loss and downstream rework vs. a linear chain? (Prior: **supported for parallelizable pipelines, contested/negative for strictly-sequential ones — §4.6**; no direct head-to-head exists, so this is the experiment that would settle it.)
- **RQ5 — Producer strategy.** When does best-of-N + verified selection (§4.5) beat single-candidate + revision, at equal total budget? (Prior: **the answer flips on verifier soundness — best-of-N rides the coverage curve under a sound oracle, but a noisy verifier imposes a finite-optimal-N ceiling, so revision wins — §4.5**.)

**The baseline ladder** — no agent, checklet, or route earns a permanent slot without beating the *relevant* rung on cost-adjusted holdout: **B0** strong single agent (matched tools/context/model) · **B1** fixed full loop · **B2** reduced default loop (orchestrator+builder+verifier) · **B3** static checklet bundle, no risk model · **B4** routed loop + rule-based aggregator · **B5** routed loop + calibrated risk model · **B6** verify-everything ceiling (where feasible) · **B7** human/expert reference (where feasible). **B0 is the bar most changes actually have to beat** (the fixed loops B1/B2 tend to be budget-inefficient). **Equalize budgets by metering *actual* tokens/tool-calls consumed, never nominal caps** — requested budgets can under-report true thinking tokens by ~4–5×, so nominal-cap "equalization" silently compares unequal compute. And **report cost and routing/selection quality *jointly***: a router that sends everything to the cheap tier shows large "savings" at terrible quality, so cost without a paired quality number (and routing accuracy vs. an oracle, not an LLM judge alone) is meaningless.

**Named ablations** (extends the §10.3 matrix; same harness contract) so the report can attribute gains to a *cause* rather than to extra compute: leave-one-out per role (no-planner / -architect / -researcher / -documentor) · broad-critic-only vs. specialized-checklets-only · critic advisory vs. block-capable · static vs. dynamic checklet routing · no-risk-model vs. rule-based vs. learned aggregator · **single-candidate+revision vs. best-of-N+selector** · **linear-chain vs. task-graph controller**, ideally factored as a 2×2×2 (controller × staleness-propagation × explicit-edge-state-passing) so "graph structure" isn't confounded with "explicit state passing" · audit-off vs. audit-on. Each result must name which lever moved: producer output, context, routing, checklets, aggregation, compute, verification, stopping, or human review. The §10.5 promotion gates and the §5.7 independence and oracle predicates are the decision rules these experiments feed.

## RQ6 — cross-system handoff: the foreign-verifier experiment

The §7.5 manifest is a hypothesis until a foreign verifier matches a same-system one. The metric is **agreement between the foreign verifier (manifest-only) and the same-system verifier (full context)** on the same accept/reject decisions — reported as **Cohen's κ *and* raw agreement** (κ deflates under the skewed marginals you get when most artifacts pass), and always **as a fraction of the measured oracle ceiling** (same-system test–retest κ), never as an absolute: because the verifier is a judge, "the foreign verifier recovers X% of same-system reliability" is the only honest claim. Three things the protocol must include: a **prose-only NULL** (manifest stripped to a bare intent string — if the full manifest doesn't beat it, the structured fields are dead weight); a **field ablation** for the *minimal sufficient manifest* (smallest field set statistically indistinguishable from the full one — drop consumed-fact hashes and `CONSUMED_FACT_MISMATCH` attribution collapses; drop exit_state and you can't separate "unfinished" from "wrong"); and, in the ceiling regime, **representational-drift injection** (key reorder, number reformat, language-tag case, schema bump) measuring reconciliation rate under canonicalized addressing vs. false-mismatch rate under raw hashing. The **headline is Δκ(floor→ceiling)** with CI: small → handoff is genuinely stateless; large with ceiling κ collapsing toward the NULL → "cross-system" is mostly same-system, and the spec must mandate a shared canonicalization profile as a precondition. **Build the floor regime first — it is a kill switch:** if floor κ doesn't reach a pre-registered fraction (~0.9) of the oracle ceiling, stop, because no canonicalization work saves a manifest that can't make a stranger agree on byte-identical canon. (The test set must be balanced across decision classes with injected, known-cause defects — genuine passes plus consumed-fact / exit-condition / invariant violations — so attribution can be scored against ground truth.)

## RQ7–RQ14 — the Agent Fabric program + experimental contract

Your Core already has RQ1–RQ6 covering dynamic composition, selective verification, specialized checklets, graph orchestration, producer strategy and cross-system verification. It also has the correct strong-single-agent baseline and named ablation discipline.

The Agent Fabric research should extend those questions rather than duplicate them.

#### RQ7 — Runtime-substrate independence

**Question**

Can the Assurance Kernel produce statistically equivalent acceptance decisions when the same artifact graph is executed through different agent runtimes?

Compare:

1. Native single-agent execution.

2. Ruflo-backed execution.

3. Your own Agent Fabric.

4. Direct deterministic service execution where applicable.

Hold constant:

* models,

* tools,

* context manifests,

* artifact contracts,

* gate versions,

* budgets,

* task seeds.

Measure:

* final acceptance agreement,

* artifact-contract pass rate,

* quality,

* cost,

* latency,

* trace completeness,

* unrecoverable runtime failures,

* variance between repeated runs.

The critical result is not byte-identical generated artifacts. It is whether execution backends remain assurance-equivalent after verification.

A strong outcome would show that the Assurance Kernel is genuinely runtime-neutral. A weak outcome would reveal that hidden runtime behavior materially changes verification outcomes.

#### RQ8 — Capability routing versus role routing

**Question**

Does capability-based agent and model routing outperform fixed role-based assignment under heterogeneous workloads?

Treatments:

1. Fixed model for every task.

2. Fixed Ruflo-style agent-type mapping.

3. Heuristic capability router.

4. Learned capability/model router.

5. Verification-aware router using predicted downstream verification burden.

Measure:

* final quality,

* actual token and tool cost,

* latency,

* route regret against a post-hoc oracle,

* escalation frequency,

* hard-verification volume,

* high-severity misses.

Define route regret as:

```
cost-adjusted outcome of best feasible executor
− cost-adjusted outcome of selected executor
```

The important boundary condition is task heterogeneity. Routing should provide little value on homogeneous tasks and more value when tasks vary materially in complexity, tool needs and domain. RouteLLM supports model-level cost–quality routing; the deeper contribution would be routing against total downstream system cost, including verification and repair.

#### RQ9 — When do swarms earn their keep?

**Question**

Which measurable task properties predict whether a swarm outperforms a matched single agent?

Manipulate four task properties:

*  decomposability,

*  coupling between subtasks,

*  context overlap,

*  verifier soundness.

Compare:

*  one strong agent,

*  independent partitioned workers,

*  best-of-N producers,

*  hierarchical supervisor,

*  specialist panel,

*  mesh-style collaboration.

Do not treat topology as a label. Define its actual semantics:

*  who owns each artifact,

*  what messages are exchanged,

*  when agents may revise another agent’s output,

*  how results are merged,

*  what ends the run.

Measure:

*  quality,

*  cost,

*  wall-clock latency,

*  duplicate work,

*  inter-agent message volume,

*  handoff loss,

*  error amplification,

*  merge failures,

*  revision burden.

MAST makes this especially important because it found that many multi-agent failures arise from system design, inter-agent misalignment, and verification or termination—not merely weak models.

The output should be a topology-selection rule, not a conclusion that one topology is universally best.

For example:

```
Low coupling + high decomposability:
    partitioned parallel swarm

High variance + strong verifier:
    best-of-N

High coupling + shared context:
    single agent or tightly controlled hierarchy

Weak verifier:
    avoid large best-of-N or consensus selection
```

#### RQ10 — Durable execution under faults

**Question**

Does an event-sourced, artifact-addressed runtime recover more correctly from execution faults than mutable workflow-state coordination?

Inject:

*  process termination,

*  rate limits,

*  provider timeout,

*  malformed structured output,

*  duplicated message delivery,

*  partial artifact writes,

*  tool failure,

*  worker lease expiry,

*  stale dependency use,

*  human-review timeout.

Compare:

1.  Linear in-memory execution.

2.  Ruflo-style persisted workflow state.

3.  Artifact graph with node-level checkpoints.

4.  Artifact graph plus idempotency, leases and event ledger.

Measure:

*  successful recovery rate,

*  duplicate side effects,

*  accepted work lost,

*  stale artifacts released,

*  unnecessary recomputation,

*  recovery latency,

*  manual intervention rate.

The critical safety property should be:

```
A recovered run may repeat pure computation,
but may not duplicate an external side effect
or silently reuse an invalidated artifact.
```

This question lies between agent research and classical distributed workflow systems. Agent papers often report task success but give much less attention to crash consistency, idempotency and partial-failure semantics.

#### RQ11 — Memory utility versus memory contamination (decided: governed memory lifecycle; §7.6)

**Question.** Which memory-write and promotion policy maximizes cross-run utility while minimizing stale, poisoned, or wrongly generalized memory?

**Decision.** The policy vocabulary is canonical; the winner is not. **Directly supported**: indiscriminate add-all growth underperforms even a fixed bank; selective, verification-gated writing is the adaptive minimum; consolidation is a model-generated transformation needing its own verification; memory is a durable low-prevalence attack surface (poison retrievable later without hurting aggregate benign metrics); TTL alone is not a defense — fresh poison is fresh, old canon can be valid. **Best high-consequence hypothesis, not a proven winner**: isolated candidate branches + explicit promotion (`M4`) — it must beat equally strong verified writeback (`M3`) on harmful promotion, negative transfer, propagation, or detection delay at acceptable lifecycle cost, or M3 suffices and the branch machinery is rejected. **Non-negotiable regardless of outcome**: protected canon/policy has **no automatic runtime write path** (§7.6 firewall) — runtime memory may propose, never mutate.

**Treatment vocabulary (`MEM-*`).** Base write/authority policies `M0` stateless · `M1` curated read-only · `M2` success-writeback · `M3` verified writeback · `M4` governed promotion (branch + canary + explicit promote). Lifecycle overlays `D0` none · `D1` age/TTL decay · `D2` event-driven invalidation + revalidation · `D3` = D1+D2. Decay is an **overlay on retention, not a sixth peer write policy** — the stub's six arms map to M0–M4 with D crossed. Memory policy + snapshot are part of frozen executor identity: two runs with different memory authority are different executors and must not be compared as one.

**Injections.** Stale procedures · contradictions · malicious retrieved instructions (write-path injection through ordinary queries — no DB access needed) · cross-tenant/domain leakage · model-specific patterns · tool/schema-invalidated patterns · consolidation poisoning · delayed activation · **false corroboration** (many descendants of one poisoned episode) · promoter-targeting.

**Measure.** Future-task gain + token reduction (utility) · retrieval precision **and** presented-vs-materially-used causal attribution · negative transfer · stale-use + poisoned-propagation rates · `R_fp^(a)`, κ_p, `L_fp` stratified by authority (§6.7) · contamination reproduction number `R_c` (subcritical <1 required) · detection→quarantine→descendant-revocation times `T_d/T_q/T_r` and harmful uses `N_h` · canon/policy contamination = **0 by architecture** · full lifecycle cost (verify + canary + monitor + rollback + human) against the M1 curated baseline.

**Promotion gates.** M4 promotes to default only if it beats M3 at matched transition-verifier strength on a safety dimension worth its overhead; adaptive memory at all only if it beats M1 after full lifecycle cost; any memory only if it beats M0 on future-task gain. High-authority memory promotion uses the §6.6 certificate machinery on frozen memory-governance bundles (`R_fp` certificates) — the RQ13 apparatus, second instantiation.

**Stop / revert ladder.** `learned promotion → transparent governed promotion (M4) → verified writeback (M3) → curated read-only (M1) → no memory (M0)`. Trigger reversion on: `R_c ≥ 1` after mitigation · descendant revocation unreliable · detection/quarantine time over the consequence budget · compatibility filtering leaking across model/tool/schema/tenant/domain · consolidated memory losing to retained raw episodes · governance cost consuming the savings that justified memory · retrieval vs. causal use indistinguishable (harm attribution impossible). Any automatic path mutating protected canon/policy is an architecture-stopping defect at every rung. Mixed-effects estimators, survival models, priors, and universal TTL/support-count/canary numbers stay in the RQ11 supporting report.

#### RQ12 — Plugin and tool capability containment (decided: the runtime tool broker; §4A)

**Question.** Can a contract-governed Runtime Tool Broker prevent unauthorized effects without making legitimate execution prohibitively expensive?

**Decision.** Yes, **conditionally — architecturally supported, unproven on this workload**. The broker (§4A) does not stop prompt injection from influencing reasoning; it changes what compromise *buys*: `compromised reasoning ⇏ authorized external effect`. Production posture: **AUTH-T5** wherever a verifier verdict can authorize a consequential transition (release, deploy, publish, pay, message, permission change) · **AUTH-T4** for mixed-trust plugins without a real producer–verifier division · **AUTH-T3** only as a migration floor or inside an equivalent outer containment boundary · T1/T2 are baselines or broker-hidden compatibility shims. The answer flips to *false* under: incomplete mediation, overbroad actions (`run_task(command)` re-creates ambient authority), wrong policy issuance, credential leakage into model-visible context, syscall-filter-only "sandboxes," untrusted parameters selecting the consequential target, role labels without principal separation, or intolerable contract-engineering burden ("not prohibitive" includes onboarding/versioning/sandbox-parity hours, not just latency).

**Treatment ladder (`AUTH-T*`).** `T1` ambient unrestricted tools · `T2` pinned direct-launch allowlist · `T3` typed named actions (closed schemas, canonicalization, stable mechanical errors, no raw surfaces) · `T4` = T3 + per-call `AuthorityGrant` + resource/parameter binding + action-specific sandbox profiles + mediated egress + broker-owned effect adapters + effect slots · `T5` = T4 + distinct producer/verifier principals + controller-owned release. **Run the deterministic suite before any LLM trial**: property tests, grammar fuzzing, path/URL canonicalization, state-machine exploration, concurrent replay, capability-mismatch matrices, crash-point schedules.

**Attack corpus.** Prompt injection · tool-name spoofing · parameter smuggling · path traversal · unauthorized egress · privilege escalation · malicious plugin metadata **and correctly-signed malicious plugins** (provenance proves identity, never benignity) · verifier attempting producer-side writes or direct release · fresh-key duplicate effects · mechanical-failure→approval conversion attempts · audience/token confusion.

**Measure (independent oracles, never broker self-report).** Policy-violation success rate · sensitive-exposure rate · unauthorized side-effect rate per severity class (`R_ue,j`) · **mechanical-to-approval conversion rate (must be 0)** · role-boundary violation rate (must be 0) · duplicate-effect + outcome_unknown rates · false-denial rate + legitimate-completion margin · human-approval volume · warm/cold sandbox latency · action onboarding + upgrade hours. `broker=denied ∧ state=changed` is a containment bypass, not a logging bug.

**Promotion gates.** No reachable raw execution surface · zero mechanical→approval conversions · zero verifier-side producer mutation · replay/cardinality invariants pass · critical `R_ue,j` upper bounds within preregistered budgets · completion + false-denial margins pass · platform sandbox coverage attested (unsupported control ⇒ action unavailable, never silently equivalent) · results survive held-out plugins, schemas, and attack compositions · total-path + engineering cost within budget.

**Stop / simplify.** Any bypassable effect path or ambient credential → reject the containment claim outright. T4 not materially beating an honest T3 under malicious-plugin/ambient-authority attacks (after ruling out accidental T3 isolation and weak attacks) → reject T4 as built. Producer and verifier sharing effective credentials/writable state/release → reject T5 as built. No meaningful independent verdict or consequential producer→verifier transition → simplify to T4. Environment already supplies equivalent per-run isolation and plugins aren't independently hostile → T3 inside the outer sandbox is acceptable but **may not be marketed as broker-provided malicious-plugin containment**. Rare-event statistics rarely certify `R_ue`; containment rests on invariant testing + independent oracles + audit UCBs — say so, don't overclaim. Token-format bake-offs, OS-substrate comparisons, noninterference tests, and the human fatigue study stay in the RQ12 supporting report.

#### RQ13 — Verification-budget-aware scheduling (decided: scheduler proposes, governor authorizes; §6.6)

**Question.** Can a scheduler jointly choose producers, specialists, tools, candidates, checklets, probers, hard verification, repair, human review, and stopping while preserving a certified false-waiver bound?

**Decision.** Yes, **conditionally — only via structural separation**: a performance **scheduler** optimizes and may *propose* `stop_accept`; an independent **certification governor** (§6.6) alone authorizes unverified terminal acceptance, and only when a valid `AuthorityCertificate` covers the exact frozen `ControlPolicyBundle` × task stratum × terminal artifact hash × epoch. A risk penalty inside a scheduler reward encourages empirical safety; it cannot manufacture a finite-sample guarantee. **What is certified is a complete frozen policy bundle (or a preregistered family of bundles under LTT), never a bag of actions** — recombining actions from several certified bundles is an uncertified policy. `κ=0` treatments (verify-all, fail-closed) have no defined `R_fw`; they are safe fallbacks, not certified waiver policies.

**Treatment ladder (`SCHED-T*`).** `T1` strong producer, verify-all · `T2` cheap producer, verify-all · `T3` pinned off-the-shelf role/model router + static verification (product-neutral definition; vendor identity is experimental metadata only) · `T4` dynamic routing + static verification · `T5` **transparent frozen VoI controller + governor** (§6.4 acquisition rules; every would-be waiver adjudicated in shadow until certified) · `T6` learned non-myopic policy + same governor. **Build and certify T5 before attempting T6** — if T5 cannot beat T4, added RL will learn noise, shortcuts, or cost gaming. T5≈T6 is a *simplification result*, not a failure.

**Measure.** `A/V/W/B_ref` exactly as §1 (exact-object discipline) · `R_fw` per required stratum (UCB) · κ + useful-waiver coverage · completion + acceptance floors (fail-closed gaming detector) · quality noninferiority vs. matched baselines · **total path cost** (scheduler + producers + specialists + tools + checklets + probers + hard verify + repair + escalation + human + delay + failure) and amortized cost including training/calibration/shadow-adjudication · p50/p95 latency with queue vs. service decomposition · hard-verifier + human volume · route regret + decision-time propensities for off-policy evaluation. Strong-producer break-even is an accounting identity to *measure* (§4.5), not assume.

**Promotion gates (in order).** Valid certificate per required stratum → κ ≥ κ_min and completion/acceptance floors → quality noninferiority → held-out-family + later-temporal-slice stability → only then Pareto frontier improvement (cost, p95, verifier volume, human volume). Any material change to scheduler/governor/producer/prompts/checklets/verifier/repair/schema/task-mix/reference protocol expires the certificate (§4.6 invalidation bus). Underpowered high-risk strata run always-verify; certify only predeclared material strata, report per-route diagnostics.

**Stop / simplify.** T5 beats T4 on no qualified frontier dimension → keep T4. T6 beats T5 on nothing under the same action pool + governor → reject learned scheduling. Certified useful coverage below the preregistered minimum, verifier error ≈ α, scheduler overhead > saved verification+human work, recertification cadence uneconomical, or audit UCB approaching internal α → shrink the waiver region or fall back to verify-all. Oracle-poor strata state their certificate as **reference-relative** (§6.5), never true-correctness. Grid construction, FWER procedure, sequential/weighted-conformal variants, and CMDP/RL machinery stay in the RQ13 supporting report — the Core requires the evidence and gates, not one estimator.

#### RQ14 — Federated execution transparency (decided: declared execution closure; §7.7)

**Question.** Can a remote executor produce an artifact operationally equivalent to a local execution without hidden shared state?

**Decision.** Conditionally supported architecturally; **not yet proven empirically** — the mechanism is canonical (§7.7), the equivalence claim is the experiment. The unit that crosses a boundary is a **declared execution closure**: pre-execution `ExecutionContract` (inputs, canon epochs, executor/tool identity, authority, recovery + effect semantics, acceptance rules) + isolated execution + durable effect state + post-execution `ExecutionEvidenceManifest` + independent foreign verification + release-time closure revalidation. The claim is bounded and system-relative — **never** byte-reproducibility, semantic proof from a signature, executor truthfulness, or exactly-once effects.

**Treatment ladder (`FED-X*`; boundary conditions, orthogonal to fabric topology).** `X0` local reference · `X1` remote + shared memory (information-rich ceiling, not a production target) · `X2` remote + prose handoff · `X3` remote + typed contract · `X4` = X3 + evidence manifest + foreign verification. Keep the ladder, not a full factorial: hold transport/source-facts/executor/budget fixed so **X2→X3 is a clean typing contrast and X3→X4 a clean post-execution-evidence contrast**; X1→X2 is a deliberate boundary comparison, not a component estimate. Optional negative control: prose + provenance-only attestation (signatures without typed closure must fail). Every run records `boundary_condition_id` **separately from** `fabric_treatment_id` — do **not** cross FED-X with FAB-F initially. X4's expected value is **assurance** (closure enforcement, fault recovery, effect reconciliation, stale-release prevention, attribution, disclosure accounting), not first-pass generation quality; in no-fault runs X3≈X4 is expected.

**Injections.** Schema/plugin/canon drift · dropped + duplicate delivery · worker restart mid-effect · provider substitution · commit-window crashes · undeclared-read canaries · malicious/incompetent remote executor (signed lies included).

**Measure.** The §7.7 equivalence **vector**, never one score: acceptance agreement + quality noninferiority (domain margins) · high-severity defect margin · contract-violation + undeclared-read + canary-access counts · logical-effect discrepancy/ambiguity (`N_commit(k) ≤ 1`) · foreign-verifier reproducibility **and** hidden-oracle validity (report raw agreement + transition matrix + κ/AC1 + per-verifier validity — agreement is not correctness) · disclosure (prohibited spans = 0; excess fields/bytes) · fault-conditioned recovery `R_f(B)` (a retry that duplicates an effect is not a recovery) · attribution-localization · total cost/latency last, inside the feasible set.

**Promotion gates.** All six §7.7 invariants hold on bounded exhaustive fault schedules · X4 noninferior to X0 on final outcome within preregistered domain margins · foreign-verifier validity/agreement clears the floor · zero undeclared dependencies on natural (not evaluator-authored) tasks · effect ambiguity bounded or safely stopped · disclosure within policy · cost/latency acceptable only after the above. Coding first (oracle-rich), writing second (oracle-poor stress test); replicate on research + UE5; FAB-F treatments only after the boundary mechanism and metrics are frozen.

**Stop / limit.** Kill if: X4 fails the **shared-canon floor** (can't reproduce decisions on identical content addresses) · signatures pass but planted lies are accepted (verifier not independent) · any bounded schedule violates a non-compensable invariant · matching X0 requires undeclared reads or copying nearly all local state · effect state stays ambiguous past the reconciliation budget · gains exist only on synthetic evaluator-authored contracts · both verifiers agree while failing the hidden oracle. If coding passes and writing fails, **limit the claim to oracle-rich domains** rather than weakening the standard. X4 adding no assurance over X3 at material overhead → manifest becomes optional/risk-triggered. Detailed estimators (mixed-effects, AC1, robustness curves, power) live in the RQ14 supporting report, not here.

#### Experimental contract

Use the same proof discipline already present in the Core.

**Workload**

Begin with two domains rather than all four:

*  coding, because it has strong executable oracles;

*  writing, because it is oracle-poor and tests human-review and anti-homogenization behavior.

Then replicate on research and UE5.

Stratify tasks by:

```
complexity
decomposability
coupling
external-evidence dependence
oracle strength
side-effect risk
context size
historical failure class
```

**Baselines**

Retain the Core’s existing baseline ladder. In particular, the strong matched single agent remains the primary null hypothesis—not an intentionally weak baseline.

For Agent Fabric experiments, the most important treatments are:

```
F0  Strong native single agent
F1  Fixed Ruflo-style full agent set
F2  Reduced static fabric
F3  Capability-routed fabric
F4  Capability-routed fabric + artifact graph
F5  Fabric + deterministic assurance
F6  Fabric + calibrated risk-aware scheduler
F7  Verify-everything ceiling
```

Do not replace the BASE-B0…B7 namespace; these can be treatment labels inside the Agent Fabric study.

**Treatment-namespace registry (binding).** RQ11–RQ14 each shipped an unlabeled `T1…Tn` ladder; unqualified they collide (AUTH-T3 “typed actions” vs. SCHED-T3 “pinned router” are unrelated). Telemetry and reports therefore record `treatment_ladder` + `treatment_id`, drawn only from: `BASE-B0…B7` (the answer ledger) · `FAB-F0…F7` (above) · `MEM-M0…M4 × MEM-D0…D3` (RQ11) · `AUTH-T1…T5` (RQ12) · `SCHED-T1…T6` (RQ13) · `FED-X0…X4` + `boundary_condition_id` (RQ14) · `COMP-L0…L3` (RQ17 compositional-assurance scope) · `CERT-D0…D6` (RQ18) · `EPI-S0…S6` + required epistemic-observability fields (RQ26). A run may carry one label per namespace (e.g., `SCHED-T5` under `FED-X0`); an unlabeled bare `T3` in any artifact is a schema violation.


**Metrics**

Use five metric families:

**Outcome**

*  final task success,

*  domain-specific quality,

*  high-severity defect escape.

**Economics**

*  actual tokens,

*  actual tool calls,

*  model cost,

*  verifier cost,

*  human minutes,

*  wall-clock latency.

**Coordination**

*  route regret,

*  handoff loss,

*  duplicate work,

*  message volume,

*  revision burden,

*  error amplification.

**Runtime reliability**

*  recovery success,

*  stale escape,

*  duplicated side effects,

*  lost accepted artifacts,

*  mean recovery time.

**Assurance**

*  false-waiver rate,

*  waiver coverage,

*  false-block rate,

*  calibrated risk,

*  policy violations,

*  audit findings.

**Statistical design**

Use paired tasks and matched budgets. Randomize model seeds and treatment order where possible. Report bootstrap confidence intervals and correct families of related tests rather than promoting components on point estimates.

Use mixed-effects analysis when combining domains:

```
fixed effects:
    orchestration treatment
    task coupling
    decomposability
    oracle strength

random effects:
    task
    model
    domain
```

The most important interactions are likely:

```
swarm × decomposability
swarm × coupling
best-of-N × verifier soundness
memory × environment drift
routing × task heterogeneity
fault recovery × side-effect class
```



---

## E1 — Evidence record: `ibkr-auto-trader` (July 7–26, 2026)

**What was deployed.** A partial v1.5-era runtime — the collab engine transplanted *into* the product repository (PR #8: 14,044 lines, 80 files, merged in under 60 seconds) — run at `AUTH-T1` posture: ambient tools, self-waiver, autonomous self-merge (0 human reviews across 37 PRs; 15 of 35 merged in ≤2 minutes; one PR merged red), operational config in gitignored `seats.json`, and the governor living inside the governed. **Treatment labels are retroactive**: the run was not registered under any ladder in advance.

**Outcome.** 0 of 11 autonomous runs reached done (all stops were provider/tooling plumbing, none reviewer judgment). Seven audit rounds, ~44 candidates, non-convergent (volume outgrew ~50% closure; INT-030 re-derived from scratch as CPR-001 eight days later). Final grade **F**; final commit literally named `failed experiment`; repository archived. Headline churn: 40,987 additions vs 1,385 deletions across six PRs (13.6:1 tooling:product); 1,041 passing tests at grade F; the standing pyright-debt figure (372) off by >2× from measurement (167).

**Mechanisms observed (each now a spec control).** Self-attestation — the park state written every second, read by nothing, its test asserting on its own writer (→ INV-G6, §5.8 wiring proof). Inert assurance — 594 tested lines never invoked; silent fallback to legacy (→ INV-G5 applied to wiring, §5.8). Interpreter escape — "read-only" reviewers writing source via allowed `python`/`uv` (→ AUTH-T4's motivation, realized). Dropped finding — a confirmed risk defect discarded because an *unrelated* lane timed out; "0 defects" reported thereafter (→ incomplete = `outcome_unknown`, §5.8). Identity bleed — `cur.update()` merge-not-replace; fresh run wearing a dead run's face; lease/projection never reconciled; freeze bypassed by the Start path *after* the failed-experiment commit (→ `run_record`/`lease` machines, §8A). Telemetry without producer authority — arbitrary child processes appending live-run events (→ INV-A7). No wire ever touched — every provider test monkeypatched; 8/16 adapter commits were wire-format patches (→ non-hermetic boundary rule). Terminal-reason collapse — nine conditions reported as `capped` (→ `driver_terminal_reasons`). Additive repair — every incident produced a new subsystem; old paths never deleted (→ INV-G8, `handoff_contract`).

**What held.** pyright invoked by a human (caught the fail-open the builder, reviewer, and three adversarial lanes all signed), human review generally, and git provenance — independent executable checking and protected human review under the §5.7 profile model. The same-model review configurations used in the incident did not catch the fail-open. Salvaged *concepts* (not code): paper-first posture, Decimal boundaries, generation fencing, human-override ≠ verified-completion, missing-identity ≠ match.

**Ledger impact (annotations, no closures).** §6.3 warning field-confirmed · `BASE-B0` null strengthened · RQ12 threat model realized in production · RQ9 skepticism supported · §5.7 profile dimensions received their first field annotation. **Limitations:** n=1; uncontrolled; overdetermined (with no firewall, no principals, and no independent oracle simultaneously absent, no single missing control can be credited with any single failure); partial instantiation, so this is evidence about *deployment posture*, not a test of the architecture. Disposition: archived as incident record; credentials rotated; collab directory not ported.

---

## RQ15 — Instantiation certification (opened by E1)

**Question.** Can spec-instantiation be certified — wiring proofs (§5.8) plus scheduled non-hermetic oracles — at a total cost that beats the audit flywheel it replaces?

**Why it may be engineering, not research.** The individual mechanisms are known practice (consumer-driven contract tests, live canary checks, conformance attestation by independent process). The open question is economic and compositional: E1's counterfactual baseline is seven audit rounds producing ~44 well-scoped candidates *without convergence* — evidence-generating, not convergence-generating. A certification regime wins if an instantiation's conformance claims survive one independent audit **without producing a correction ledger**, at lower total cost than the flywheel. If a pilot on the next runtime settles that in an afternoon of measurement, this row closes as engineering and leaves.

**Decision evidence.** (a) Cost of the wiring-proof + non-hermetic suite for one conformant slice; (b) whether `core_lint`-class mechanical checks + one external black-box oracle catch the E1 bug classes (self-attestation, inert wiring, identity bleed) *before* an audit does; (c) audit-flywheel cost on the same slice as control. No treatment ladder minted until (a)–(c) justify one.

---


## RQ17 — Compositional sufficiency across spines and domain packs

**Question.** Under what dependency, evidence-sharing, state-sharing, authority-overlap, global-property, and usage-domain conditions can independently validated domain-pack policies, certificates, and Core assurance spines receive maximum modular reuse without new interaction-specific certification, and when is interaction-aware certification required?

**Decision.** The Core must not treat `independently certified` as equivalent to `safe in composition`. The canonical architectural mechanism is an explicit **composition manifest + interaction graph + proof-obligation gate**. Existing certificates receive modular credit only to the extent that the configured composition introduces no uncovered assurance-relevant interaction. The certification process may still require an integration acceptance step even when no new interaction-specific evidence is needed.

The key distinction is:

```text
PROPERTY composition
    !=
EVIDENCE composition
    !=
CERTIFICATE / ARGUMENT composition
```

A pair of packs may link cleanly at the assurance-case level while failing semantically because of shared state, or may preserve its properties while overstating confidence because both certificates depend on the same simulator, verifier, corpus, model family, or threat assumption.

### Composition-scope ladder (`COMP-L*`)

`COMP-L0` **modular reuse + compatibility validation** — all interaction obligations are already discharged by certified contracts, frames/invariants, authority bounds, evidence-dependence treatment, global-property composition rules, and usage-domain checks. No new interaction-specific substantive evidence is created, although the governing assurance regime may still require an integration/acceptance step.

`COMP-L1` **local interaction certification** — one or more bounded pairwise/small-scope interactions require an explicit discharge artifact: contract implication, state-stability proof, authority-attenuation proof, provenance/dependence treatment, fixed policy order, or equivalent.

`COMP-L2` **configuration-level integration certification** — the assurance claim depends on a declared multi-pack configuration: shared mutable resources, authority tier crossing, probabilistic joint claims, nontrivial hyperproperties, substantial joint state, or usage-domain coupling.

`COMP-L3` **end-to-end joint recertification** — system-wide behavior cannot be soundly reduced to bounded interaction certificates, or top-level assumptions/authority/hyperproperties have materially changed.

The ladder is about **additional assurance scope**, not a promise that `COMP-L0` eliminates whatever integration acceptance a standard, regulator, or deployment policy separately requires.

### Formal component object

For pack or spine component $M_i$, record

$$
M_i=
(A_i,G_i,E_i,R_i,W_i,U_i,\Theta_i,\Pi_i),
$$

where:

- $A_i$: assumptions;
- $G_i$: guarantees;
- $E_i$: evidence and provenance dependencies;
- $R_i$: state read-set;
- $W_i$: state write-set;
- $U_i$: authority/capability set and delegation semantics;
- $\Theta_i$: certified usage/configuration envelope;
- $\Pi_i$: policy-combination semantics.

The composition is represented as a typed interaction hypergraph

$$
\mathcal G=
(V,E_D,E_S,E_A,E_E,E_H),
$$

for dependency, state, authority, evidence, and global/hyperproperty interactions. Hyperedges are required because an unsafe effect can arise only when three or more packs and the spine are present simultaneously.

Every unresolved hyperedge carries:

```text
affected components
interaction type
required proof obligation
minimum COMP-L level
certificate / evidence references
```

### Canonical reuse predicate

Define:

$$
\boxed{
\begin{aligned}
\mathrm{ReuseEligible}(M,Q)\iff{}&
\mathrm{ContractClosed}(M)\\
&\land\mathrm{StateStable}(M)\\
&\land\mathrm{AuthorityBounded}(M)\\
&\land\mathrm{EvidenceSound}(M)\\
&\land\mathrm{GlobalPropertyProven}(M,Q)\\
&\land\mathrm{UsageDomainValid}(M).
\end{aligned}
}
$$

This means **maximum modular reuse is justified**. It does not imply that a regulator or assurance standard waives all system-integration activity.

#### Dependency closure

For each component $i$,

$$
\boxed{
Env\land
\bigwedge_{j\in Pred(i)}G_j
\models A_i.
}
$$

Use the predecessor set rather than only pairwise $G_j\Rightarrow A_i$: one assumption can legitimately be discharged by several guarantees jointly.

Acyclic discharged dependencies are the easy case. A strongly connected dependency component is not automatically invalid, but it requires an explicit sound circular-reasoning artifact such as temporal induction, a safety-closure check, an inductive invariant, a ranking/well-founded argument, or another theorem whose hypotheses are recorded. Thus:

$$
Cycle\land\neg WellFoundedDischarge
\Rightarrow
\text{interaction trigger}.
$$

#### State stability

For potential read/write interference, let $I_i(s)$ be an invariant relied upon by component $i$ and $T_j(s,s')$ an allowed foreign transition. Require:

$$
\boxed{
I_i(s)\land T_j(s,s')
\Rightarrow I_i(s').
}
$$

A static detector may first compute, for read/write incidence matrices $R,W$,

$$
X_S=WR^\top+WW^\top.
$$

A nonzero entry is a **candidate interaction**, not a failure. Disjoint footprints can be discharged by frame/separation reasoning; disciplined shared state requires an invariant/ownership/serialization proof.

Append-only or content-addressed state reduces destructive mutation but is not automatically semantically noninterfering. Structural monotonicity

$$
s\preceq s'
$$

does not imply

$$
I(s)\Rightarrow I(s')
$$

unless the relevant invariant/query is itself monotone.

#### Authority boundedness

For effective authority closure $Cl(U)$, require:

$$
Cl\left(\bigcup_i U_i\right)
\subseteq U_{\max}.
$$

In sufficiently expressive protection models, exact authority-leakage reachability is undecidable. A production linter therefore MUST either use a restricted decidable authority language or a sound conservative over-approximation

$$
Cl(U)\subseteq\widehat{Cl}(U)
$$

and accept only when

$$
\widehat{Cl}(U)\subseteq U_{\max}.
$$

Descriptive overlap such as

$$
AO(A,B)=
\frac{|Auth(A)\cap Auth(B)|}
{|Auth(A)\cup Auth(B)|}
$$

may help rank review effort but is not a safety proof. A one-capability overlap can be catastrophic while broad read-only overlap is benign. The safety-relevant test is whether composed authority crosses the declared ceiling or harm tier.

Policy combination semantics must also be explicit. If

$$
P_i\otimes P_j\ne P_j\otimes P_i,
$$

deployment order is part of the certified configuration and MUST be fixed/revalidated.

#### Evidence dependence

Evidence reuse does **not** require statistical independence in all cases. It requires that material dependence is represented consistently with the inference being made.

The canonical condition is:

$$
\boxed{
DependenceAccountedFor(E_1,\ldots,E_n),
}
$$

not `all evidence is independent`.

A structural evidence-incidence matrix $B$ can identify shared provenance via

$$
M_E=BB^\top,
$$

but provenance overlap does not by itself justify a numerical correlation coefficient. The analysis ladder is:

```text
E0  provenance overlap
E1  causal/common-cause dependence model
E2  calibrated quantitative dependence model, only where data support it
```

Knight–Leveson-style common-mode results are the warning: independent development does not imply independent failure. Shared verifier, corpus, simulator, specification, model family, test oracle, or assessor cannot silently be counted as independent corroboration.

For probabilistic claims, a full joint distribution is not always necessary. With only marginals,

$$
\max(0,p_A+p_B-1)
\le
P(A\cap B)
\le
\min(p_A,p_B).
$$

If a worst-case dependence bound already establishes the required claim, no richer joint model is required. Otherwise use an explicit joint/multi-objective argument or escalate.

#### Global properties and hyperproperties

Local component claims must establish the actual global property:

$$
\boxed{
\bigwedge_iG_i\models Q
}
$$

either directly or under a named compositional theorem whose side conditions are discharged.

Relational properties such as noninterference and other hyperproperties are default-escalate because ordinary local trace properties do not generally imply them. They are not universally non-compositional: a MAKS-style, hypersafety, UC-style, or other applicable theorem may discharge the interaction when its exact hypotheses hold.

#### Usage-domain closure

For certified envelope $\Theta_i$,

$$
\boxed{
\theta_{\mathrm{actual}}\in\Theta_i
\quad\forall i.
}
$$

If composition transforms parameters,

$$
\theta'=f(\theta_1,\ldots,\theta_n),
$$

require

$$
f(\Theta_1,\ldots,\Theta_n)
\subseteq
\Theta_{\mathrm{certified}}.
$$

A reused component outside its assumptions of use is not saved by the fact that its binary, model, or policy file is unchanged.

### Uncovered-interaction set and trigger predicate

Define

$$
U=
U_D\cup U_S\cup U_A\cup U_E\cup U_H\cup U_\Theta.
$$

`COMP-L0` requires $U=\varnothing$ and the global-property implication to hold.

Interaction-aware certification is triggered when any unresolved condition holds:

1. shared mutable state outside a certified frame/invariant/serialization protocol;
2. cyclic dependency without a sound well-founded discharge;
3. an undischarged contract assumption;
4. authority closure may cross the certified ceiling or harm tier;
5. shared tool/credential surface uses ambient rather than provenance-bound per-call authority;
6. material evidence dependence is ignored or double-counted;
7. a probabilistic system claim cannot be established by conservative dependence bounds or a justified joint/multi-objective model;
8. policy combination is order-dependent and the order is not fixed/certified;
9. a required hyperproperty/global relational claim lacks an applicable discharged composition theorem;
10. actual configuration escapes any component usage domain / assumption-of-use envelope;
11. a cryptographic/protocol composition theorem is used outside its setup, concurrency, adversary, or joint-state assumptions.

Failure of a trigger test means **the existing certificates are insufficient**, not that the system is proven unsafe.

### Minimum interaction-specific certification scope

The composition gate should not automatically recertify the whole system. Let unresolved interaction hyperedges be $e_t\in U$, candidate certification scopes be $S_j$, level $\ell$, and cost $c(S_j,\ell)$. A research/engineering optimizer may solve

$$
\boxed{
\min
\sum_{j,\ell}
c(S_j,\ell)z_{j,\ell}
}
$$

subject to

$$
\forall e_t\in U:
\quad
\sum_{\substack{j:e_t\subseteq S_j\\\ell\ge\ell_t}}
z_{j,\ell}\ge1,
\qquad
z_{j,\ell}\in\{0,1\}.
$$

This is a weighted set-cover formulation of the practical question:

> What is the smallest additional assurance campaign that covers every new interaction?

The runtime MAY use a simpler conservative algorithm initially; the key requirement is that recertification scope is derived from the interaction graph rather than guessed globally.

### Metrics

The RQ17 experiment SHOULD report:

- **contract-discharge completeness**
  $$
  CDC=
  \frac{\text{discharged assumptions}}
       {\text{required assumptions}};
  $$
  `CDC < 1` is always a trigger;
- unresolved interaction count by type;
- false-negative rate of the linter against seeded known interactions;
- false-escalation rate / unnecessary `COMP-L2/L3` assignments;
- certification scope size and cost versus manual whole-system recertification;
- time to locate the causal interaction;
- authority tier crossings;
- evidence-provenance overlap and whether dependence treatment changed the assurance conclusion;
- usage-domain escapes;
- hyperproperty theorem coverage;
- regression rate after pack/version changes.

Interaction-surface cardinality and authority-overlap ratios are workload-prioritization metrics only. They MUST NOT be promoted into safety thresholds without empirical validation.

### Injections and experimental protocol

Seed pack/spine configurations with known interaction causes:

```text
hidden dependency assumption
multi-predecessor assumption
circular dependency with and without a valid invariant
read/write overlap on a relied-upon invariant
append-only update that changes downstream semantics
ambient shared credential
attenuated capability versus privilege-amplifying delegation
first-applicable / order-sensitive policy change
shared verifier/corpus/simulator provenance
probabilistic guarantees with unknown dependence
noninterference / hyperproperty interaction
usage-domain escape
three-pack-only authority or state hyperedge
version change that should affect only one certification closure
```

For each case compare:

1. independent component certificates only;
2. manual expert composition review;
3. registry linter + theorem/proof artifacts;
4. conservative whole-system recertification control.

The primary safety endpoint is **missed material interaction**. The primary efficiency endpoint is **additional certified scope/cost conditional on zero missed non-compensable interactions in the seeded suite**.

### Promotion / release gates

A new pack, spine version, or configured pack set may receive modular credit only when:

1. every participating component has a signed `PackCompositionManifest`;
2. the interaction graph is reproducible from those manifests;
3. all dependency assumptions are discharged;
4. every state-sharing edge has disjointness, ownership, serialization, or invariant-stability evidence;
5. authority closure is proven in a restricted model or conservatively bounded;
6. material evidence dependence is represented;
7. global properties/hyperproperties have an applicable proof rule;
8. actual usage remains inside all declared envelopes;
9. every unresolved edge has an interaction certificate at or above its required `COMP-L` level; and
10. the governing deployment/certification process's required integration acceptance has completed.

### Stop / simplify

Reject or simplify the mechanism if:

- the linter misses a seeded non-compensable interaction;
- authority analysis pretends to be exact while operating in an undecidable/unbounded model;
- provenance overlap is converted into a fabricated correlation coefficient without calibration data;
- `COMP-L0` is presented as "no integration assurance of any kind";
- append-only storage is treated as proof of semantic noninterference;
- pairwise-only analysis misses higher-order hyperedges;
- certification-scope optimization costs more than conservative recertification at the deployment's scale.

If the full hypergraph optimizer provides no material advantage, retain the typed manifests, triggers, and conservative closure computation and drop the optimizer.


### Research grounding

The RQ17 architecture is grounded in several distinct literatures rather than one universal composition theorem:

- *Benveniste, A., Caillaud, B., Nickovic, D., et al. (2012). Contracts for System Design. [HAL](https://inria.hal.science/hal-00757488/)* — contract composition, compatibility, assumptions, guarantees, and refinement.
- *de Alfaro, L., & Henzinger, T. A. (2001). Interface Automata. ESEC/FSE. [ACM](https://dl.acm.org/doi/abs/10.1145/503271.503226)* — compatibility and independent implementability under interface refinement.
- *Brookes, S., & O'Hearn, P. W. (2016). Concurrent Separation Logic. ACM SIGLOG News. [ACM](https://dl.acm.org/doi/abs/10.1145/2984450.2984457)* — local reasoning, ownership, and controlled shared-state interference.
- *Mantel, H. (2002). On the Composition of Secure Systems. IEEE Symposium on Security and Privacy. [IEEE](https://ieeexplore.ieee.org/abstract/document/1004364/)* — theorem-backed composition results for specified security-property classes.
- *Clarkson, M. R., & Schneider, F. B. (2010). Hyperproperties. Journal of Computer Security. [DOI](https://doi.org/10.3233/JCS-2009-0393)* — relational security properties beyond one-trace safety.
- *D'Osualdo, E., Farzan, A., & Dreyer, D. (2022). Proving Hypersafety Compositionally. Proceedings of the ACM on Programming Languages. [ACM](https://dl.acm.org/doi/10.1145/3563298)* — compositional reasoning for hypersafety.
- *Bonatti, P., De Capitani di Vimercati, S., & Samarati, P. (2002). An Algebra for Composing Access Control Policies. ACM TISSEC. [ACM](https://dl.acm.org/doi/abs/10.1145/504909.504910)* — formal access-control policy combination.
- *Harrison, M. A., Ruzzo, W. L., & Ullman, J. D. (1976). Protection in Operating Systems. Communications of the ACM. [ACM](https://dl.acm.org/doi/abs/10.1145/360303.360333)* — general safety/reachability limits for expressive protection systems.
- *Knight, J. C., & Leveson, N. G. (1986). An Experimental Evaluation of the Assumption of Independence in Multiversion Programming. IEEE Transactions on Software Engineering. [IEEE](https://ieeexplore.ieee.org/abstract/document/6312924/)* — empirical common-mode failure despite independent development.
- *Kwiatkowska, M., Norman, G., Parker, D., & Qu, H. (2013). Compositional Probabilistic Verification Through Multi-Objective Model Checking. Information and Computation, 232, 38–65. [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0890540113001120)* — compositional quantitative reasoning without naïve scalar-probability conjunction.
- *Bate, I., & Kelly, T. (2003). Architectural Considerations in the Certification of Modular Systems. Reliability Engineering & System Safety. [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0951832003000942)* — modular certification and integration-level assurance.
- *Ron, J., Baudry, B., & Monperrus, M. (2026). N-Version Programming with Coding Agents. [arXiv](https://arxiv.org/abs/2606.20158)* — modern evidence that implementation diversity does not justify an independence assumption, while diversity may still provide practical benefit.

The engineering rule taken from this body of work is deliberately narrower than any single source: **local certificates are reusable only to the extent that every interaction-relevant assumption/effect is covered by an applicable contract, theorem, dependence treatment, or integration certificate.**


### Relationship to RQ18 — orthogonal assurance axes

RQ17 and RQ18 answer different lifecycle questions and SHOULD be recorded independently.

```text
RQ17 / COMP-L*
    = how much interaction-specific assurance does this configured composition require?

RQ18 / CERT-D*
    = after the configuration changes, how much of the prior assurance can be reused
      and what is the cheapest sound path to a successor certificate?
```

A configuration may therefore carry both labels, for example:

```text
COMP-L2
CERT-D3
```

meaning that the configuration requires integration-level interaction assurance, while a later change may be handled by interaction-aware differential recertification rather than by rerunning the whole system.

The shared mathematical object is the typed assurance/interaction graph. RQ17 uses it **horizontally** across simultaneously composed packs and spines; RQ18 uses it **temporally** to determine which claims, evidence, and interaction certificates are affected by a change. In the canonical implementation, an `InteractionCertificate` is bound to the successor `CertifiedContextHash`; an old interaction certificate therefore cannot authorize a changed configuration merely because its pack IDs are unchanged.

The combined rule is:

$$
\boxed{
\text{composition scope}
\times
\text{change-recertification strategy}
\rightarrow
\text{successor assurance obligation}
}
$$

with the old certificate remaining non-authorizing whenever the exact certified context changes.

### What remains open

The architectural rule is sufficiently supported to fold: **reuse is interaction-conditional, and uncovered assurance-relevant edges trigger additional assurance**. The empirical work remains:

```text
How conservative should the authority abstraction be?
Which evidence-dependence metadata predicts materially different conclusions?
How often are higher-order hyperedges needed beyond pairwise checks?
What is the false-escalation cost of default-refuting hyperproperties?
How much certification cost does minimum-scope analysis actually save?
Which theorem/proof artifacts can be checked mechanically at registry time?
What pack/version changes can be proven not to affect existing interaction certificates?
```

There is no canonical scalar "composability score." The output is a set of discharged or unresolved proof obligations and the minimum defensible certification scope.

---

## RQ18 — Certification durability under drift and change

**Question.** How long do Core certificates remain valid under changes to models, prompts, tools, schemas, policies, task distributions, reference protocols, and dependent artifacts, and what invalidation and recertification strategy minimizes assurance cost while preventing stale certification from authorizing materially changed behavior?

**Decision.** There is no defensible universal certificate lifetime. The architecture should separate **certificate-instance validity** from **assurance-claim continuity**:

$$
\boxed{
\text{configuration identity}
\neq
\text{behavioral equivalence}
\neq
\text{assurance-claim continuity}
}
$$

A certificate instance is exact-context authority. If any observable dependency in its certified context changes, the old certificate stops authorizing immediately. But that does **not** imply that every prior claim or evidence item is discarded. The successor context is analyzed for causal and interaction impact; unaffected evidence whose assumptions and reference protocol remain valid may be carried forward; only the missing assurance is reacquired; and a **new** certificate is issued for the new context.

The canonical lifecycle is therefore:

```text
change
  -> exact-context mismatch
  -> old certificate stops authorizing
  -> claim + interaction impact analysis
  -> retain still-applicable evidence
  -> cheapest sufficient delta evidence
  -> successor certificate
  -> least authority justified by currently valid claims
```

Time-to-live remains only a backstop for the residue the runtime cannot reliably observe, chiefly opaque provider-side model/serving changes and some forms of slow environmental drift. Continuous behavioral monitoring MUST use anytime-valid statistics when it contributes to a continuing risk claim; repeated ordinary p-value peeking is not a valid permanent monitor.

### Identity, behavior, and assurance are different objects

Let the certification-relevant Core state be

$$
x=(m,p,t,s,\pi,\mu,r,a),
$$

where $m$ is model/serving state, $p$ prompts, $t$ tools, $s$ schemas/data contracts, $\pi$ policies, $\mu$ task/environment distribution, $r$ reference/evaluation protocol, and $a$ dependent artifacts/certificates.

A certificate is conceptually

$$
C_x=
\langle
H(x),Q,\Omega,A,E,G,\Delta^+,F,\Pi,R
\rangle,
$$

with:

- $H(x)$: exact certified-context identity;
- $Q$: assurance claims;
- $\Omega$: certified operating/task envelope;
- $A$: assumptions;
- $E$: evidence;
- $G$: typed assurance-dependency / causal structure;
- $\Delta^+$: predeclared change families with bounded roll-forward procedures;
- $F$: freshness obligations;
- $\Pi$: authority enabled by the claims;
- $R$: risk/confidence requirements.

The exact-context invariant is:

$$
H(x')\neq H(x)
\Rightarrow
C_x\not\vdash Authorization(x').
$$

But:

$$
H(x')\neq H(x)
\not\Rightarrow
E_x=\varnothing,
$$

and it does not imply that every $q\in Q$ must be reproved from zero.

This resolves the central tension between **fail-closed content addressing** and **differential recertification**: the old authority object dies; reusable assurance knowledge may survive into a successor certificate.

### Certified Context Hash (`CCH`)

The implementation hypothesis is a Merkle-style **Certified Context Hash** over every observable dependency that can change a certified claim or its authority:

```text
model provider + resolved served version/digest
prompt/system-prompt/template digests
tool implementation + interface-contract digests
schema/data-contract versions
effective policy + harm hierarchy / authorization configuration
reference/eval protocol + judge model/prompt where applicable
dependency-certificate context hashes
canonicalization / runtime profile when claim-relevant
declared operating-envelope identifier
```

A CCH comparison is exact for the question:

> Is this still the same certified configuration?

It is **not** an estimator of material behavioral distance. A harmless byte change can alter $H$ while preserving the claim; an opaque provider can alter behavior while leaving visible identifiers unchanged. Therefore the CCH is the **identity invalidator**, not the entire recertification policy.

For stochastic behavioral probes, hash the **probe specification** and baseline identity, not raw random outputs:

```text
sentinel-set version
sampling/decoding protocol
representation
distance statistic
reference baseline
sequential detector version
risk threshold
```

The live observation is then evaluated statistically.

### Change-axis semantics

The eight RQ18 axes remain distinct.

| Axis | Old certificate | Default successor scope |
|---|---|---|
| Model weights / resolved model identity | exact certificate void | model-dependent claims + interactions |
| Silent serving-stack change | restrict/suspend when detector or TTL condition fires | behavioral differential evaluation |
| Prompt/system prompt | exact certificate void | claims whose causal paths traverse changed prompt + interactions |
| Tool/API implementation or action surface | exact certificate void | tool consumers, integration claims, affected authority paths |
| Schema/data contract | exact certificate void | semantic consumers/producers; not merely syntax-compatible nodes |
| Policy / authorization criterion | exact certificate void immediately | all property-specific policy-dependent claims |
| Task/environment distribution | statistical claims may become unsupported without byte change | distribution-sensitive claims by protected stratum |
| Reference/eval protocol | affected evidence/certificates unsupported | rerun claims whose meaning depended on changed reference |
| Dependency certificate/artifact | transitive exact-context invalidation | mechanically derived downstream assurance closure |

A more restrictive policy may preserve some monotone safety properties if

$$
Allowed(\pi')\subseteq Allowed(\pi),
$$

but that does not automatically preserve utility, completion, routing, or availability claims. Monotonicity is property-specific.

### Treatment ladder (`CERT-D*`)

`CERT-D0` **TTL-only** — fixed age-based expiry, no content-addressed dependency identity. Deliberately weak/unsafe baseline.

`CERT-D1` **CCH + global recertification** — exact-context invalidation on observable dependency change, then rerun the full certification suite. Strong safety baseline; intentionally expensive.

`CERT-D2` **CCH + dependency-closure recertification** — derive affected claims transitively; preserve evidence outside the closure under explicit applicability/assumption checks.

`CERT-D3` **interaction-aware differential recertification** — D2 + typed causal hypergraph + interaction closure so jointly unsafe changes cannot hide behind component-local passes.

`CERT-D4` **bounded semantic change envelopes** — D3 + claim-specific semantic distance / robustness margins / predeclared transformation classes that permit cheap successor-certificate roll-forward without preserving the old certificate instance.

`CERT-D5` **hybrid hidden-drift posture** — D4 + anytime-valid sentinels/fingerprints/distribution monitoring + harm/opacity-scaled TTL only for residual unobservable state.

`CERT-D6` **adaptive minimum-evidence recovery** — D5 + transparent value-of-information / constrained recertification optimizer; a learned POMDP policy is an optional later arm and MUST NOT precede a transparent controller that establishes measurable headroom.

Promotion should proceed D1 → D2 → D3 → D4 → D5 before D6. If a simpler rung matches the next rung on stale-authority risk and total lifecycle cost, the extra machinery is rejected.

### Typed assurance hypergraph and `CertificationClosure⁺`

A plain repository dependency DAG is insufficient. Claims can depend jointly on multiple components:

$$
\{Model,Prompt,Tool\}\rightarrow q.
$$

Represent assurance structure as a typed directed hypergraph whose nodes can include:

```text
components
assumptions
evidence
reference protocols
datasets
claims
certificates
authority permissions
operating envelopes
```

and whose edges distinguish causal, evidence, assumption, composition, reference, and authority dependencies.

For change $\delta$, define semantic effects $S_\delta$. The ordinary closure is

$$
CertificationClosure(\delta)
=
Reach_G(S_\delta).
$$

Then add interactions:

$$
\boxed{
CertificationClosure^+(\delta)
=
DependencyClosure(\delta)
\cup
InteractionClosure(\delta).
}
$$

Causal direction matters. If routing feeds telemetry but telemetry cannot affect routing, a telemetry-only change must not invalidate routing claims merely because the components are connected operationally.

### Interaction effects

Independent local safety does not imply safe composition:

$$
Safe(\delta_i)\land Safe(\delta_j)
\not\Rightarrow
Safe(\delta_i\circ\delta_j).
$$

For response $f$, estimate pairwise interaction:

$$
I_{ij}
=
f(x_i',x_j')
-f(x_i',x_j)
-f(x_i,x_j')
+f(x_i,x_j).
$$

If

$$
|I_{ij}|>\tau_{ij},
$$

separate recertification is insufficient.

The experiment may also evaluate Sobol indices, functional ANOVA, Shapley interaction measures, or higher-order finite differences. A useful research metric is **certification modularity**: the proportion of assurance-relevant outcome variance attributable to first-order rather than interaction effects. Low modularity predicts high recertification coupling.

### Semantic distance and assurance margin

A code diff is not certification distance. Define a claim-specific pseudometric

$$
d_q(x,x').
$$

Candidate distances include:

- model decision-disagreement probability on the certified task slice;
- policy action-set symmetric difference;
- tool observable-contract distance;
- semantic schema compatibility;
- Wasserstein/MMD/energy distance for task or output distributions.

For claim $q$, define assurance margin

$$
g_q(x)
=
ObservedAssurance_q(x)-RequiredAssurance_q,
\qquad
\gamma_q=g_q(x)>0.
$$

If sensitivity can be bounded by

$$
|g_q(x')-g_q(x)|
\le
L_q\,d_q(x,x'),
$$

then

$$
\boxed{
d_q(x,x')
<
r_q
=
\frac{\gamma_q}{L_q}
}
$$

is a sufficient condition for the underlying claim to remain on the safe side of its decision boundary.

This **robustness radius does not keep the old certificate alive**. It can justify a cheap successor-certificate proof obligation.

The experiment must compare these sophisticated distances against simpler baselines. If simple stratum-specific disagreement/effect-size measures predict certification failure equally well, retain the simpler estimators.

### Certified change envelopes and cumulative safety

Let $\Delta^+$ be predeclared transformations with bounded validation protocols. Membership means:

> a cheap, specified successor-certification procedure is permitted.

It never means the old exact-context certificate magically survives.

Model evolution as

$$
x_{t+1}=F(x_t,\delta_t).
$$

Let $K$ be a certified region. A strong cumulative-change property is robust invariance:

$$
\boxed{
F(K,\Delta^+)\subseteq K.
}
$$

This addresses the case where each update is independently permitted but the sequence eventually leaves the original assurance envelope.

RQ18 should estimate the **envelope escape rate** under seeded cumulative modifications and reject any predeclared change class that cannot maintain its claimed cumulative bound.

### Distribution drift

For original workload $P_0$, define uncertainty set

$$
\mathcal U(P_0,\epsilon)
=
\{Q:D(P_0,Q)\le\epsilon\}.
$$

A robust distribution-dependent claim is conceptually

$$
\inf_{Q\in\mathcal U}
Performance(Q)\ge\tau.
$$

Where an appropriate Lipschitz relation can be justified,

$$
|\mathbb E_P[\ell]-\mathbb E_Q[\ell]|
\le
L D(P,Q)
$$

can translate assurance margin into a certified drift radius. The program MUST reject a chosen distance when it fails to predict externally observed claim degradation better than simpler stratified monitoring.

### Anytime-valid hidden-drift monitoring

Permanent monitoring cannot repeatedly reuse fixed-sample tests without inflating false alarms. Candidate monitors include e-processes, test martingales, confidence sequences, weighted-conformal changepoint methods, or another method with an explicit anytime-valid error guarantee.

For an e-process $E_t$,

$$
P_{H_0}
\left(
\sup_t E_t\ge\frac1\alpha
\right)
\le\alpha.
$$

Use this only when the sampling assumptions hold. Sequential validity does not repair a biased sentinel stream.

The three observability regimes are:

```text
observable deterministic dependency change
    -> CCH / authority invalidation

observable stochastic behavior
    -> anytime-valid behavioral monitor

unobservable residual state
    -> risk-based TTL / fail-closed backstop
```

### Stale-authority risk budget

The primary safety quantity is not certificate age. It is

$$
\boxed{
R_{\mathrm{stale}}
=
P(
\text{authority active}
\land
\text{supporting prerequisite claim false}
).
}
$$

Require

$$
R_{\mathrm{stale}}\le\epsilon_{\mathrm{Core}}
$$

with tighter budgets for higher-harm authority:

$$
\epsilon_{\mathrm{high}}\ll\epsilon_{\mathrm{low}}.
$$

TTL can then be treated as one control in the residual-risk budget. Under a simple hidden-change hazard model $\lambda$,

$$
P(\text{hidden invalidation before }T)
=
1-e^{-\lambda T},
$$

so a backstop can be selected from

$$
1-e^{-\lambda T}\le\epsilon.
$$

This is an intuition / candidate model, not a canonical exponential assumption.

### Evidence applicability, provenance, and correlation

Evidence $e$ is reusable only if its applicability remains valid. A minimal conceptual rule is

$$
Reuse(e,\delta)=1
$$

only when:

$$
Assumptions_e(x')=TRUE
$$

and all changed dependencies are either outside $Dependencies(e)$ or covered by a validated invariance argument.

Evidence records SHOULD retain:

```text
claim IDs
dependency IDs/digests
assumptions
reference-protocol identity
dataset/evidence-family identity
freshness contract
confidence/bound
correlation/common-cause group
prior certificate lineage
```

Multiple observations from one benchmark or reference family are not independent merely because they come from different verifiers. If

$$
D\rightarrow E_1,E_2,E_3,
$$

confidence aggregation must account for the shared cause. A simple minimum-of-dependencies rule may remain a conservative governance bound, but it is not a universal probabilistic composition law.

### Minimum-evidence recertification

Let affected claims be $Q_\delta$, candidate tests $T=\{t_1,\ldots,t_n\}$, and costs $c_j$.

A simple weighted-set-cover approximation is

$$
\min_y \sum_j c_jy_j
$$

subject to sufficient coverage of every impacted claim.

The stronger target is

$$
\boxed{
T^\star
=
\arg\min_T Cost(T)
}
$$

subject to

$$
P(
q\text{ valid}
\mid
E_{\mathrm{retained}},E_T
)
\ge
1-\epsilon_q
\qquad
\forall q\in Q_\delta.
$$

Candidate acquisition ordering may use expected information gain:

$$
IG(T)
=
H(Q\mid E)
-
\mathbb E_T[H(Q\mid E,T)]
$$

and prioritize approximately

$$
IG(T)/Cost(T).
$$

D6 earns operational status only if it lowers total lifecycle cost without worsening stale-authority risk, detection delay, or protected-stratum coverage relative to a transparent fixed cascade.

### POMDP / condition-based maintenance formulation

The recertification decision is partially observable.

Candidate hidden state:

$$
S_t\in
\{
valid,\ degraded,\ materially\ changed,\ unsafe
\}.
$$

Observations:

```text
CCH state
sentinel/fingerprint evidence
production drift
external/provider attestation
incidents
audit outcomes
```

Actions:

```text
continue
restrict
screen
delta-recertify
full-recertify
revoke
```

A conceptual loss is

$$
L=
C_{\mathrm{verification}}
+
C_{\mathrm{latency}}
+
C_{\mathrm{downtime}}
+
\lambda_h C_{\mathrm{stale-authority}}.
$$

The harm tier changes $\lambda_h$. This can make shorter TTLs, broader screens, or immediate full recertification emerge from the risk model rather than from arbitrary fixed rules.

A learned policy MUST NOT replace a transparent condition-based controller unless it demonstrates qualified headroom under the same governor and stale-risk constraints.

### Certificate states and authority lattice

Use at least:

```text
VALID
RESTRICTED
SUSPENDED
REVOKED
SUPERSEDED
```

`SUPERSEDED` preserves the historical fact that $C_x$ was valid for $x$ while preventing it from authorizing $x'$.

Let authority sets be ordered by inclusion:

$$
A_1\preceq A_2
\iff
A_1\subseteq A_2.
$$

Given currently valid claims $Q_v$,

$$
Authority(Q_v)
=
\max_{\preceq}
\{
A:
Prerequisites(A)\subseteq Q_v
\}.
$$

The required monotonicity invariant is:

$$
Q'_{v}\subseteq Q_v
\Rightarrow
Authority(Q'_v)\preceq Authority(Q_v).
$$

**Loss of assurance or increasing uncertainty may never increase authority.**

### Experimental factors

Do not begin with a full factorial. Start with single-axis changes and pairwise interactions around production-like operating points, then expand only where the interaction screen justifies it.

```text
change axis
semantic magnitude
harm tier
dependency opacity
claim assurance margin
task-distribution shift
evidence/reference-family overlap
component coupling
interaction strength
monitor power
recertification cost
change cadence
```

### Injection battery

Use known-cause changes whose true assurance relevance is controlled.

```text
large harmless code/config diff
one-token policy change with material authority effect
whitespace / formatting-only prompt change
prompt instruction-precedence change
provider alias held constant while served distribution changes
quantization / kernel / hardware serving change
tool implementation change preserving interface but altering side effect
tool addition that expands agent action space
syntactically additive schema with semantic downstream effect
schema change proven semantic no-op for a target claim
judge/reference-protocol replacement
benchmark contamination / evaluator drift
task-distribution shift without artifact mutation
dependency certificate supersession
two individually safe changes with unsafe interaction
many individually allowed changes whose sequence leaves the envelope
correlated evidence from one root benchmark presented as multiple corroborations
stale certificate presented after policy or reference-protocol change
false behavioral alarm from stochastic sampling
withheld / delayed change notification
```

Every injected case should carry hidden ground truth for which claims truly require recertification.

### Primary estimands and metrics

**Stale-authority risk**

$$
R_{\mathrm{stale}}
=
P(
Authority=ON
\land
PrerequisiteClaim=FALSE
).
$$

**Invalidation precision**

$$
Precision_{\mathrm{inv}}
=
\frac{
\text{materially affected claims invalidated}
}{
\text{all claims invalidated}
}.
$$

**Invalidation recall**

$$
Recall_{\mathrm{inv}}
=
\frac{
\text{materially affected claims invalidated}
}{
\text{all materially affected claims}
}.
$$

Recall is weighted more heavily because a false negative can preserve stale authority.

**Evidence reuse ratio**

$$
ReuseRatio
=
\frac{
\text{valid prior evidence reused}
}{
\text{eligible prior evidence}
}.
$$

**Recertification amplification**

$$
RA
=
\frac{
\text{claims/tests recertified}
}{
\text{claims materially impacted}
}.
$$

**Interaction miss rate** — unsafe joint modifications that component-local recertification would have approved.

**Envelope escape rate** — permitted change sequences that leave the claimed certified region.

**Time to detect invalidating change** (`TTD`).

**False-invalidation rate** after scoped recertification.

**Certified-context coverage** — fraction of the actual assurance-relevant runtime surface captured by CCH / explicit monitored assumptions.

**Assurance debt** — harm-weighted unsupported/restricted certificate authority still awaiting resolution; production policy should normally drive this toward zero for consequential authority.

**Recertification cost**

```text
compute
eval samples
tool calls
human minutes
wall-clock
downtime / restricted-operation cost
engineering maintenance
```

**Assurance efficiency**

$$
\eta_A
=
RiskReduction/AssuranceCost.
$$

**Certification modularity** — degree to which claim changes are explained by first-order component effects rather than interaction terms.

### Certificate half-life

Half-life is a descriptive operations metric, not the validity rule.

$$
S_C(t)
=
P(
\text{certificate class encounters no invalidating condition by }t
),
$$

$$
T_{1/2}
=
\inf\{t:S_C(t)\le0.5\}.
$$

A short empirical half-life identifies unstable dependencies, excess coupling, weak abstraction boundaries, opaque providers, or an overly narrow change envelope. It does not itself force expiration at $T_{1/2}$.

### Promotion criteria

RQ18 mechanisms earn canonical operational status only if, on held-out change families:

1. exact-context changes never leave the old certificate authorizing the new context;
2. invalidation recall meets the harm-tier bound;
3. interaction traps are detected at the preregistered rate;
4. evidence carry-forward never reuses evidence with broken assumptions or changed reference meaning;
5. hidden-drift monitoring satisfies its stated anytime-valid false-alarm guarantee and required detection-power/delay target;
6. protected strata never depend on an underpowered monitor or recertification sample;
7. successor certificates bind to the new exact context and retained-evidence lineage;
8. authority monotonicity holds under every simulated evidence-loss / degradation path;
9. differential recertification lowers total lifecycle cost relative to full recertification at comparable stale-authority risk; and
10. any semantic-distance / robustness-envelope machinery beats simpler change-class + scoped-eval baselines before being retained.

### Stop / simplify ladder

```text
adaptive minimum-evidence optimizer (CERT-D6)
    ↓
hybrid monitored bounded-envelope recertification (CERT-D5)
    ↓
interaction-aware bounded differential recertification (CERT-D4/D3)
    ↓
dependency-closure differential recertification (CERT-D2)
    ↓
exact-context invalidation + full recertification (CERT-D1)
```

Revert down the ladder when:

```text
semantic distance fails to predict claim failure
interaction estimator is underpowered or too expensive
change-envelope escape rate is non-negligible
evidence-applicability graph cannot be kept complete
behavioral fingerprinting is unstable or easily evaded
monitor detection delay exceeds the consequence budget
recertification optimizer saves little or increases stale-risk UCB
correlation model is unidentifiable and conservative fallback is cheaper
lifecycle governance cost exceeds the savings from differential recertification
```

`CERT-D0` TTL-only is never a production fallback for consequential authority; it is an experimental null.

### Primary decision questions

RQ18 closes only when the program can answer, by certificate class and protected task slice:

```text
Which observable dependencies must enter the CCH?
Which hidden dependencies require stochastic monitoring or TTL?
What is the measured invalidation precision/recall of CertificationClosure+?
Which interaction classes defeat component-local recertification?
Which claim classes admit useful semantic robustness radii?
Which recurrent modifications admit safe predeclared roll-forward envelopes?
How much old evidence remains valid after each change class?
What is the cheapest evidence acquisition policy that restores each claim?
What residual stale-authority risk remains under silent provider/environment drift?
How does harm tier change the economically optimal detection and recertification policy?
How many changes can accumulate before the certified invariant region is left?
When does full recertification become cheaper than maintaining differential-certification machinery?
```

A universal certificate lifetime is not a valid closure criterion.



## RQ26 — Closed-loop self-improvement stability and feedback monoculture

**Question.** Under repeated **trace → selection → training → evaluation → deployment** cycles, under what conditions does the portfolio converge toward lower *externally grounded* error rather than toward internally self-consistent but correlated mistakes, evaluator preferences, selection artifacts, or deployment-induced distribution shift? What minimum **rate, diversity, and causal independence of exogenous evidence** is needed to keep the adaptive process epistemically stable? Which signals reveal approaching monoculture before ordinary internal success metrics deteriorate?

**Decision.** The architecture can decide the boundary but not yet the numerical stability threshold. **Canonical now:** authenticated production traces are observations, not truth; recursive evidence retains causal provenance; teacher/verifier self-confirmation does not create independent gold; development, policy-development, certification, confirmation, and production-audit roles remain separated; routing propensities or an equivalent support representation are recorded where counterfactual routing claims are made; policy-safe exploration may preserve observability where justified; the Factory produces candidates only; and promotion remains external to the learning loop. **Still open:** the minimum effective external-information rate, how to discount correlated evidence, which lineage/diversity measures predict failure earliest, how much exploration is needed to preserve counterfactual support, and what control policy gives the cheapest stable portfolio.

There is **no canonical fixed percentage** of human, real, or oracle data. Raw mixture proportion is an inadequate quantity because nominally separate observations may share the same causal error source. The object to estimate is effective independent epistemic information per protected slice and adaptation interval.

The failure of interest is broader than recursive synthetic-data collapse:

```text
producer generates
        ↓
verifier accepts
        ↓
accepted trace enters training
        ↓
specialist inherits pattern
        ↓
router increasingly selects specialist
        ↓
future trace distribution changes
        ↓
verifier successor inherits related evidence
        ↓
internal agreement rises
```

while:

```text
fresh external correctness stays flat or worsens.
```

### Treatment ladder (`EPI-S*`)

`EPI-S0` **closed recursive loop** — selected production traces + endogenous learned verification; no fresh exogenous correction beyond the initial seed corpus. This is a deliberately unsafe research control and MUST remain isolated from consequential production promotion.

`EPI-S1` **persistent epistemic roots** — S0 + original independently grounded training examples are retained rather than recursively replaced.

`EPI-S2` **fresh external audit** — S1 + a continuing uniform external audit stream excluded from training; tests whether degradation can be detected without feeding the answer back into the learner.

`EPI-S3` **fresh external training anchor** — S2 + a policy-eligible fraction of fresh independently grounded evidence may enter training through the normal data-qualification pipeline.

`EPI-S4` **anchor + counterfactual support** — S3 + controlled policy-safe route exploration or paired shadow evaluation sufficient to retain observable alternatives.

`EPI-S5` **anchor + evaluator-lineage separation** — S4 + explicit separation between principal producer/teacher ancestry and the evidence families used for promotion/certification.

`EPI-S6` **adaptive epistemic controller** — S5 + audit rate, exploration rate, promotion cadence, external-label acquisition, or route exposure change in response to preregistered stability diagnostics.

S6 MUST NOT be attempted as an unrestricted learned controller before transparent rule-based interventions establish that the measured signals predict external degradation. If a fixed S3–S5 policy is sufficient, S6 is a simplification failure and should be rejected.

### Experimental factors

Cross the ladder only with factors needed to estimate the stability boundary:

```text
external-evidence rate
external-evidence reliability
evidence-family correlation
producer/verifier lineage overlap
router exploration rate
specialist traffic concentration
synthetic-data accumulation vs. replacement
task-distribution drift
oracle strength
tail prevalence
promotion cadence
```

Do not begin with a full combinatorial factorial. First estimate one-variable dose-response curves around the current production-like operating point, then investigate interactions that materially move the stability boundary.

### Injections

Inject controlled failure modes with known causal provenance:

```text
shared producer/verifier blind spot
teacher systematic factual error
incorrect but internally coherent rubric preference
rare-class suppression
tail-category under-sampling
router selection feedback
specialist takeover
synthetic-source duplication
same-source “independent” verifier agreement
model-family convergence
stale external-world fact
provider/model-family change
human-rubric bias
source-corpus bias
performative user/environment response
fresh external contradiction
```

The injected defect MUST have a hidden external oracle or adjudication protocol wherever the experiment claims true correctness rather than reference-relative agreement.

### Primary estimand

The primary endpoint is **fresh externally grounded risk**, not internal verifier pass rate.

For protected stratum $s$:

$$
R_{\mathrm{ext},s}(t)
=
\mathbb E[
\ell_t
\mid
X\in s,\;
\text{fresh external reference}
].
$$

A generation counts as genuine capability improvement only if external risk is noninferior or improves under the preregistered margin while required coverage floors remain satisfied.

Internal pass rate, verifier agreement, router confidence, frontier substitution, and training loss are diagnostics, never primary evidence of epistemic improvement.

### Stability diagnostics

This RQ may evaluate multiple candidate estimators. The Research Program does not assume any one is canonical.

**Lineage**

- externally rooted evidence fraction;
- recursive ancestry depth;
- evidence-family concentration;
- effective number of independent root families;
- producer/verifier/teacher lineage overlap;
- fraction of labels whose ultimate correctness source is another portfolio model.

**Routing**

- route propensity/support;
- effective off-policy sample size;
- traffic entropy;
- specialist concentration;
- fraction of the eligible model set that has become counterfactually unobservable;
- random/shadow-route versus production-route outcome gap.

**Disagreement and residual dependence**

- pairwise residual-error correlation;
- unique-catch rate;
- leading covariance-eigenvalue share;
- covariance effective rank;
- internal-consensus versus external-reference disagreement.

**Calibration**

- Brier/ECE or appropriate calibration statistic on fresh external audit;
- calibration by lineage and task stratum;
- internal-calibration versus external-calibration divergence;
- selective-risk curve under fresh reference labels.

**Tail behavior**

- worst protected-stratum risk;
- CVaR or another preregistered tail-risk functional;
- tail acceptance/completion coverage;
- chronological holdout gap;
- novelty/OOD performance.

**Distribution**

- incoming-task versus training-data distribution divergence;
- pre-routing versus post-selection distribution divergence;
- fresh-time-slice drift;
- deployment-induced outcome shift.

**Audit**

- fresh-audit versus internal-pass divergence;
- later label-reversal rate;
- audit effective sample size;
- time from injected external contradiction to detection;
- number of adaptive promotions occurring before detection.

### Research-only mathematical diagnostics

The supporting RQ26 report may evaluate

$$
\rho(D F)
$$

for local closed-loop gain;

$$
\rho(Q)
$$

for recursive lineage persistence;

$$
I(Y;E_t\mid H_t)
$$

for fresh epistemic information contributed by exogenous evidence;

$$
\frac{\lambda_1(\Sigma)}{\operatorname{tr}\Sigma}
\quad\text{and}\quad
r_{\mathrm{eff}}(\Sigma)
$$

for common-mode correlated error; and

$$
W_p(
P_t^{\mathrm{incoming}},
P_t^{\mathrm{training}}
)
$$

for selection-induced distribution distortion.

These are candidate research measurements. A promotion MUST NOT depend on one merely because it appears mathematically attractive. Each earns operational status only after showing predictive validity beyond simpler baselines.

### Early-warning condition

The canonical monoculture warning pattern is:

```text
internal pass rate ↑
internal agreement ↑
router confidence ↑
specialist concentration ↑
```

while one or more of:

```text
fresh external risk ↑
external calibration ↓
effective evidence-root diversity ↓
counterfactual support ↓
residual-error effective rank ↓
tail coverage ↓
chronological performance ↓
```

moves in the adverse direction.

Call this **epistemic decoupling**.

Epistemic decoupling SHOULD trigger investigation or exposure reduction before the normal terminal-quality threshold is violated.

### Promotion gates

A recursively trained router, producer, specialist, or verifier may increase production exposure only after the normal Core promotion hierarchy passes and:

1. the affected evaluation slices contain the preregistered amount of fresh independently grounded evidence;
2. external-risk and coverage bounds pass on those slices;
3. the candidate has not obtained its principal correctness claim solely from its own descendant evidence family;
4. the counterfactual claims used to justify routing changes have sufficient logging-policy support;
5. no declared lineage/evaluation contamination condition is unresolved;
6. protected tail-risk requirements pass; and
7. audit cadence is sufficient to detect a material regression before the next consequential adaptation boundary.

Cost, latency, frontier substitution, GPU savings, or verifier-volume reduction are considered only after these conditions pass.

### Stop / revert

Stop recursive expansion or move down the ladder when any of the following occurs:

```text
fresh external risk rises while internal pass rate rises
external calibration deteriorates while internal calibration appears stable
counterfactual effective sample size falls below its declared floor
external evidence-root diversity collapses
recursive lineage becomes effectively closed
one common residual-error mode increasingly dominates the verifier portfolio
tail-risk or tail-coverage bounds fail
fresh audit cannot keep pace with promotion cadence
later independent labels reverse an increasing share of “verified” training examples
```

Fallback ladder:

```text
EPI-S6 adaptive recursive improvement
        ↓
fixed externally anchored recursion
        ↓
bounded specialist/router retraining only
        ↓
external-anchor-only retraining
        ↓
Factory shadow-only
        ↓
frozen production portfolio
```

No fallback relaxes the Core's ordinary authority or verification requirements.

### Primary decision questions

RQ26 closes only when the program can answer, by protected task slice:

```text
What is the empirical closed-loop amplification rate?
How much genuinely independent evidence is required to keep it subcritical?
How much evidence diversity matters beyond raw evidence count?
How much route exploration is required to preserve counterfactual observability?
Which early-warning statistic predicts external degradation first?
How many adaptive generations can safely occur between independently powered audits?
Which fixed control policy is sufficient before a learned adaptive controller is justified?
```

A universal human-data percentage is not a valid closure criterion.


### Integrated mathematical model and stability contract

The mathematics is folded into this RQ because it determines what the experiment must measure, but it remains **research-level machinery rather than runtime constitution**.

#### Closed-loop state

Represent generation $t$ by

$$
X_t=
\left(
P_t,\Theta_t,\Phi_t,\Pi_t,\mathcal D_t,G_t
\right),
$$

where $P_t$ is the external task/environment distribution; $\Theta_t$ the producer/specialist portfolio; $\Phi_t$ the verifier/evaluator portfolio; $\Pi_t$ the routing policy; $\mathcal D_t$ the learning/evaluation data state; and $G_t$ the causal provenance graph.

Let

$$
U_t=
(
E_t,A_t,\Xi_t,\Gamma_t
)
$$

denote controllable exogenous evidence, audit allocation, route exploration/shadowing, and promotion/adaptation cadence. With stochastic disturbance $\xi_t$,

$$
\boxed{
X_{t+1}=F(X_t,U_t,\xi_t).
}
$$

The one-dimensional intuition

$$
e_{t+1}\approx(1-\alpha_{\mathrm{eff}})g\,e_t+\eta_t
$$

is only a local simplification. Its condition

$$
(1-\alpha_{\mathrm{eff}})g<1
$$

shows why there is no universal external-data percentage: the required effective correction depends on the loop gain $g$.

#### Local stability

At an equilibrium $X^\star$,

$$
F(X^\star,U^\star)=X^\star.
$$

Linearizing:

$$
\delta X_{t+1}
=
A^\star\delta X_t+
B^\star\delta U_t+
W_t,
\qquad
A^\star=D_XF(X^\star,U^\star).
$$

A classical local stability condition is

$$
\boxed{\rho(A^\star)<1}.
$$

Because the loop is compositional, the Jacobian can be conceptualized as

$$
A^\star
=
J_{\mathcal H}
J_{\mathcal R}
J_{\mathcal T,\mathcal V}
J_{\mathcal M}
J_{\mathcal S}
J_{\mathcal G},
$$

for environment response, routing, training/verifier update, mixture construction, selection, and generation. A conservative small-gain sufficient condition is

$$
\|
J_{\mathcal H}
\|
\|
J_{\mathcal R}
\|
\|
J_{\mathcal T,\mathcal V}
\|
\|
J_{\mathcal M}
\|
\|
J_{\mathcal S}
\|
\|
J_{\mathcal G}
\|
<1.
$$

RQ26 should estimate directional gains for seeded failure modes before attempting to identify a full high-dimensional Jacobian.

#### Stable does not mean correct

Define externally grounded risk

$$
R_{\mathrm{ext}}(X)
=
\mathbb E_{(x,y)\sim P_{\mathrm{external}}}
[\ell(X;x,y)].
$$

A system can satisfy

$$
\rho(D_XF(X^\star))<1
$$

while

$$
R_{\mathrm{ext}}(X^\star)-R^\star>\epsilon.
$$

That is a **stable wrong equilibrium**. RQ26 therefore requires separate claims for dynamical stability and epistemic adequacy:

$$
\boxed{
\rho(D_XF(X^\star))<1
}
$$

and

$$
\boxed{
R_{\mathrm{ext}}(X^\star)-R^\star\le\epsilon.
}
$$

The first never substitutes for the second.

#### Lyapunov / drift formulation

For nonstationary operation, define a candidate functional

$$
V(X_t)
=
R_{\mathrm{ext}}(X_t)
+
\lambda_1C_{\mathrm{corr}}(X_t)
+
\lambda_2C_{\mathrm{lineage}}(X_t)
+
\lambda_3C_{\mathrm{tail}}(X_t).
$$

A useful research target is

$$
\mathbb E[
V(X_{t+1})\mid\mathcal F_t
]
\le
(1-\gamma)V(X_t)+b_t.
$$

If $b_t$ does not vanish, the realistic goal is bounded tracking rather than convergence to zero error.

#### Fresh epistemic information

Let $Y$ denote external truth, $H_t$ the information already present in the recursive portfolio history, and $E_t$ newly acquired external evidence. Define the conceptual fresh-information quantity

$$
\boxed{
\mathcal I_t^{\mathrm{ext}}
=
I(Y;E_t\mid H_t).
}
$$

A candidate long-run condition is

$$
\frac1T
\sum_{t=1}^{T}
I(Y;E_t\mid H_t)
\ge
\mathcal I_{\min}.
$$

This is not assumed directly estimable in production. It defines what “effective independent external evidence” means.

If later labels are only stochastic transforms of existing portfolio information,

$$
Y\rightarrow H_t\rightarrow H_{t+1},
$$

then the data-processing inequality gives

$$
I(Y;H_{t+1})\le I(Y;H_t).
$$

Recursive computation can reorganize existing information; under this model it cannot create new information about an unobserved external truth.

#### Provenance as an absorbing Markov chain

Partition normalized epistemic ancestry into internal sources and external roots:

$$
P=
\begin{pmatrix}
Q&R\\
0&I
\end{pmatrix}.
$$

The fundamental matrix is

$$
\boxed{
N=(I-Q)^{-1}.
}
$$

Expected recursive ancestry depth is

$$
\tau=N\mathbf 1,
$$

and eventual absorption into external root families is

$$
\boxed{
B=NR.
}
$$

Candidate warnings are increasing $\|\tau\|$ and

$$
\rho(Q)\rightarrow1.
$$

A closed internal class with $\rho(Q)=1$ is epistemically self-referential.

For absorption weights $B_{ij}$, define

$$
H_i=-\sum_jB_{ij}\log B_{ij},
\qquad
N_{\mathrm{root},i}^{\mathrm{eff}}
=
e^{H_i}.
$$

This is a causal-diversity measure, not merely a source count.

#### Correlated residual error

On a common independently grounded audit set, let

$$
r(x)
=
(r_1(x),\ldots,r_K(x))^\top
$$

be model/verifier residuals and

$$
\Sigma=\operatorname{Cov}(r).
$$

With eigenvalues $\lambda_1\ge\cdots\ge\lambda_K$, define

$$
\boxed{
C_{\mathrm{common}}
=
\frac{\lambda_1}{\operatorname{tr}\Sigma}.
}
$$

With

$$
p_i=\frac{\lambda_i}{\sum_j\lambda_j},
$$

define covariance effective rank

$$
\boxed{
r_{\mathrm{eff}}
=
\exp
\left(
-\sum_i p_i\log p_i
\right).
}
$$

Rising $C_{\mathrm{common}}$ or falling $r_{\mathrm{eff}}$ can reveal common-mode error while raw agreement is still rising. High-dimensional covariance estimators must be validated for the actual audit sample size.

#### Routing and counterfactual identifiability

For logging policy $\pi_0$ and target policy $\pi_1$,

$$
w_i=
\frac{\pi_1(m_i\mid x_i)}
     {\pi_0(m_i\mid x_i)}.
$$

The usual importance-sampling effective sample size is

$$
\boxed{
n_{\mathrm{eff}}
=
\frac{(\sum_iw_i)^2}{\sum_iw_i^2}.
}
$$

If overlap collapses, the comparative claim becomes unsupported even if the production router is confident.

When deployment changes outcomes or future task supply, estimate an interventional target where feasible:

$$
R(\theta,\pi)
=
\mathbb E[
\ell
\mid
\operatorname{do}(\Pi=\pi)
].
$$

#### Distribution and tail drift

A candidate selection-distortion statistic is

$$
D_{\mathrm{selection},t}
=
W_p(
P_t^{\mathrm{incoming}},
P_t^{\mathrm{training}}
).
$$

The experiment should reject this estimator if a simpler stratified divergence predicts failure equally well.

For protected stratum $S_j$,

$$
R_j(t)
=
\mathbb E[
\ell_t\mid X\in S_j
].
$$

Mean risk does not compensate for a protected-tail failure. Report protected-stratum risk and coverage, chronological holdout performance, and when justified

$$
\operatorname{CVaR}_\alpha(L_t).
$$

#### Continuous audit

For a protected error ceiling $\epsilon$, zero failures among $n$ effectively independent uniform audit items gives exact one-sided upper bound

$$
p_{\mathrm{upper}}
=
1-\delta^{1/n}.
$$

Thus

$$
n
\ge
\frac{\ln\delta}{\ln(1-\epsilon)}
\approx
\frac{-\ln\delta}{\epsilon}.
$$

At 95% confidence this is approximately the rule-of-three scale $3/\epsilon$.

The architectural question is therefore whether the audit process reaches the required power **before another consequential adaptive generation is promoted**.

For permanently monitored audits, the program may test nonnegative e-processes $E_t$ satisfying under the null

$$
\mathbb E[E_t\mid\mathcal F_{t-1}]
\le
E_{t-1}.
$$

Ville's inequality gives

$$
P_{H_0}
\left(
\sup_tE_t\ge\frac1\alpha
\right)
\le\alpha.
$$

These methods remain subordinate to valid audit sampling; sequential validity does not rescue a biased audit stream.

#### Viability region and control objective

The intended research output is an **epistemically viable operating region**, not one universal percentage:

$$
\mathcal K=
\left\{
X:
\begin{array}{l}
R_{\mathrm{ext},s}(X)\le\epsilon_s
\quad\forall s\in\mathcal S_{\mathrm{protected}},\\
C_{\mathrm{tail}}(X)\le c_{\max},\\
n_{\mathrm{eff}}^{\mathrm{route}}(X)\ge n_{\min},\\
N_{\mathrm{root}}^{\mathrm{eff}}(X)\ge k_{\min},\\
\text{fresh audit power}\ge a_{\min},\\
\text{validated stability diagnostics pass}
\end{array}
\right\}.
$$

Choose controls $U_t$ to solve conceptually

$$
\boxed{
\min_U
\mathbb E
\left[
\sum_{t=0}^{T}C(U_t)
\right]
}
$$

subject to

$$
\boxed{
P_U(
X_t\in\mathcal K
\;\forall t\le T
)
\ge1-\delta.
}
$$

The controls are external-label acquisition, audit allocation, route exploration/shadowing, training mixture, and promotion cadence.

This makes the RQ's end product a **stability map**:

$$
\boxed{
\text{task slice}
\times
\text{feedback gain}
\times
\text{evidence independence}
\times
\text{exploration}
\times
\text{audit cadence}
\longrightarrow
\text{stable / unstable / unsupported}.
}
$$

#### Simplification rule

The mathematical diagnostics earn operational status only if they predict external degradation earlier or more reliably than simpler observables. If fresh external risk, external calibration, root-family concentration, route-support effective sample size, and protected-tail metrics perform just as well, retain the simpler set.

The Core requires observable lineage, external grounding, counterfactual honesty, independent audit, and governed promotion. It does not constitutionalize one estimator.


## Open empirical tensions

Holding the line on epistemic honesty (the source corpus is careful about this, and it matters for defending the design):

- **Independent certification is not a composition theorem (RQ17).** Property, evidence, and certificate/argument composition remain distinct. `COMP-L0` means no unresolved interaction-specific proof obligation after contract/state/authority/evidence/global-property/usage-domain closure; it does not mean that a governing standard waives all integration acceptance. Authority analysis must remain restricted or conservative where exact leakage is undecidable, and evidence provenance must not be translated into fake statistical independence. The open questions are the linter's false-escalation cost, higher-order hyperedge prevalence, theorem coverage, and whether minimum-scope certification materially beats conservative whole-configuration recertification.
- **Certification durability is exact at the context boundary but empirical at the semantic boundary (RQ18).** A CCH can prove that the deployed configuration is not the one named by the old certificate; it cannot by itself prove whether behavior materially changed or how much evidence can safely carry forward. `CertificationClosure+`, interaction tests, semantic robustness radii, hidden-drift monitors, and minimum-evidence recertification remain empirical until they beat simpler full/scoped recertification baselines on stale-authority risk and lifecycle cost. The old certificate must still stop authorizing on exact-context mismatch even when a cheap successor proof is available.

- **Recursive agreement is not evidence of epistemic improvement (RQ26).** A self-improving portfolio may progressively determine which examples are observed, which outputs count as correct, what enters training, which specialists receive future traffic, and which evaluator descendants judge later generations. Internal pass rate, evaluator agreement, router confidence, and specialist substitution may therefore improve while fresh external correctness deteriorates. The minimum effective rate and causal diversity of independent evidence required to prevent this remain open. Until RQ26 establishes a stability boundary, recursively trained portfolio changes require fresh external audit, explicit evidence-family lineage, and sufficient routing support for any counterfactual performance claim. No raw human/synthetic mixture percentage is canonical.
- **Which executor capabilities and decomposition boundaries actually matter** on your real task mix is a *hypothesis*, not a result. The merge/remove priors (orchestrator↔planner, planner↔architect, critic→checklets, documentor inline) must be confirmed by holdout ablation on your data.
- **Threshold values** (`α`, the ±3/±5pp gates, κ≥0.6, reject-precision 0.90, the +20% cost ceiling) are *operating proposals*. Calibrate them on your workload before treating them as policy.
- **Pairwise vs. pointwise** is resolved *by job* (§5.2), but the right anchors, panel composition, and per-dimension κ can only be finalized after you collect human labels on your own artifacts.
- **Public benchmarks are external anchors, not production proxies.** SWE-bench / τ-bench / GAIA scores are scaffold- and harness-dependent and contamination-prone; the Anthropic +90.2% figure is an internal eval, not independently reproduced — accept the *direction*, treat the *magnitude* with caution.
- **The dominant hidden failure mode is not model weakness — it is miscalibrated waiver decisions under shift.** That is why the random-audit stream and continual recalibration are non-negotiable, even after everything passes once.
- **Adversarial generation's value is a complementarity hypothesis, not a given.** The breaker (§5.5) earns its agent cost only if it catches what the diagnostic stack misses; measure unique-catch rate and overlap per lens before making it default-on, and watch for breaker outputs collapsing onto one redundant failure class (§6.3).
- **The evidence ladder's thresholds are tunable.** *Which* evidence level earns block-authority (located? triggered? executable?) and how much evidence to demand before a finding is actionable (§5.6) trade precision against recall and producer latency — set the bar from your own seeded-defect precision/recall, not from this document.
- **The oracle-poor guarantee is a different, weaker object than the oracle-rich one.** Where no sound oracle exists, `R_fw` bounds *disagreement with a noisy human proxy*, not true failure (§6.5); the two must never be reported as the same number, and if your human raters' own inter-rater agreement is below the target, the target is unmeasurable. This is the formal cost of §5.7's oracle ceiling, and it falls hardest on the most subjective packs.
- **The high-severity labeling budget is the program's critical path, not an afterthought.** Certifying a small bound is sample-hungry (~150–400 labeled high-severity items *per domain, per tier*); the eval program is otherwise underpowered (a parity claim needs ~1,000 items, §10.3), so plan the labeling spend up front and treat any small-set result as a pilot. Most "it works" claims in this space die on statistical power, not on the mechanism.
- **Cross-system handoff is bounded twice over and never free (§7.5).** The foreign verifier is oracle-ceiling-bound, so its agreement is relative to a judge, not a proof; and canonicalization shrinks but cannot eliminate representational drift, so the floor→ceiling reliability delta (Δκ) has an irreducible floor above zero. Measure that delta before assuming an artifact that verifies at home will verify abroad, and report κ as a fraction of the oracle ceiling — never as a correctness guarantee.
- **Governed promotion has not beaten verified writeback — that is the RQ11 experiment, not a result (§7.6).** The evidence rejects add-all growth and mandates selective verified writing (`M3`); it does *not* prove branch-isolation-plus-explicit-promotion (`M4`) earns its lifecycle cost over `M3` at matched verifier strength. Adopt `M4` as the high-consequence hypothesis, but let `R_fp`, `R_c`, and detection-latency on your workload decide whether the branch machinery stays or collapses back to `M3`.
- **The learned scheduler is not the destination (§6.6).** A transparent VoI controller (`SCHED-T5`) is the *likely production endpoint*; `T6` is justified only if delayed information, action interactions, or queue dynamics create certified headroom `T5` cannot capture. `T5 ≈ T6` is a simplification result, not a failure — and certification can be feasible yet uneconomical at your volume, which is a cost decision made *after* the bound is shown feasible, never by weakening the bound.
- **Effect containment is an invariant-tested property, not a certified rate (§4A).** Rare-event statistics rarely certify a small `R_ue` from zero observations; the containment claim rests on complete mediation + independent oracles + audit UCBs and holds only under its stated assumptions (unforgeable non-amplifiable grants, sound action specs, effective sandboxing, correct policy issuance). When an assumption fails the claim does not apply — report the assumptions, do not report a fabricated bound. A confined verifier can still lie, so consequential release needs broker-checkable evidence, a reproducible trigger, a trusted verifier, a threshold of independent verifiers, or a human — separation of duties confines effects, it does not make a verdict true.
- **Verifier independence is a multidimensional profile to ablate, not assert (§5.7).** Principal, model family, prompt lineage, prior-conclusion exposure, evidence family, toolchain, execution environment, organizational separation, and oracle validation must be varied and measured separately. "Run it in a separate model" is underspecified. Each governed transition needs explicit profile predicates, and a producer self-approving at high authority is a defect regardless of prompt wording.
- **Immutable lineage and lawful deletion are in tension (§7.6).** Auditability wants append-only provenance; privacy and legal obligations may require erasure. Distinguish logical revocation/tombstoning, retention expiry, cryptographic erasure, and retained non-sensitive metadata — "never delete" is *not* universally lawful, and the compliance implementation belongs in deployment/domain packs, not a blanket core promise.
- **Governance overhead may consume the savings it protects.** Verification is cheap relative to inference, but schema design, semantic validation, version governance, sandbox parity, provider reconciliation, action onboarding, memory lifecycle cost, and human-approval burden may dominate. "Not prohibitively expensive" must count those, not just broker latency — measure total lifecycle cost, and if it exceeds the assurance benefit, simplify down the ladder rather than shipping unaffordable governance.
- **Instantiation-certification economics remain open (§5.8, RQ15).** E1 demonstrates that self-authored tests can miss inert wiring, identity bleed, and self-attestation even at high test counts. The measurable question is whether consumer-observed wiring proofs plus scheduled non-hermetic oracles catch those defect classes earlier and at lower total cost than repeated audit rounds. The comparison must count suite construction, maintenance, external canaries, audit labor, correction volume, and time to convergence.

