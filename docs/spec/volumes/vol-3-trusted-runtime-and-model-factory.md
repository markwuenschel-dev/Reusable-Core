> **Reusable Core v1.10 — Volume III: Trusted runtime and self-improving model portfolio**
>
> Normative detail for runtime and learning. Formerly *Trusted Runtime and Self-Improving Model Portfolio for Reusable Core v1.9* (RQ17/RQ18/RQ26 integrated, LaTeX-fixed).
>
> **Precedence:** the [v1.10 kernel](../reusable-core-v1.10-kernel.md) wins any conflict with this document. Internal references to "v1.9" and to sibling documents by their former names are historical; see the [supersession map](../README.md#supersession-map).
>
> **Fidelity:** everything below the end-of-header marker is the source document reproduced byte-for-byte (`Trusted_Runtime_and_Self-Improving_Model_Portfolio_for_Reusable_Core_v1_9_RQ17_RQ18_RQ26_integrated_math_latex_fixed.md`, SHA-256 `224113857693dcf2`).

<!-- v1.10 volume header end -->
# Trusted Runtime and Self-Improving Model Portfolio for Reusable Core v1.9

> **Integrated revision — 2026-08-21.** Adds RQ17 compositional-sufficiency architecture alongside the existing RQ18 certification-durability and RQ26 closed-loop epistemic-stability integrations. Exact composition closure, exact certificate-context invalidation, and fail-closed authority semantics are normative to this implementation recommendation; advanced semantic-distance, higher-order interaction, and recertification-optimization estimators remain research candidates until validated.

## Executive summary

The strongest 2026 implementation of the Reusable Core is **not an all-NVIDIA stack and not an all-Kubernetes stack**. It is a deliberately hybrid architecture in which a very small, conservative trusted computing base governs a much larger, replaceable intelligence and execution plane.

The Reusable Core v1.9 should remain the normative control plane. Its most important architectural constraints are exactly the right ones for this implementation: competence is distinct from authority; production is distinct from verification; epistemic authority is distinct from effect authority; evidence is distinct from truth; and optimization is distinct from governance. Models and agents therefore remain replaceable executors rather than trusted principals. fileciteturn0file0

My recommended architecture is:

> **Kubernetes + SPIFFE/SPIRE + OPA + KMS/Vault + PostgreSQL + a dedicated durable invalidation stream + a custom Runtime Tool Broker and Authorization Monitor set + microVM-grade isolation for hostile code, with Temporal for durable orchestration, content-addressed S3/Ceph artifacts, OpenTelemetry for diagnostics, and a replaceable inference layer using Switchyard/NIM/Dynamo or KServe/vLLM plus frontier APIs.**

The critical design decision is that **Temporal, Switchyard, NIM, Dynamo, KServe, Nemotron, frontier APIs, agent frameworks, router models, verifier models, and Model Factory training jobs are not security authorities**. Compromise of any of them may produce bad candidates, waste money, or cause availability failures, but it should not permit an unauthorized authoritative effect.

The security-critical TCB should be limited to:

1. workload identity and trust roots;
2. policy composition and policy decision enforcement;
3. cryptographic key custody;
4. Authorization Monitors, Certification Governor, Release Controller, Runtime Tool Broker and grant verification;
5. transactional effect-slot/operation state;
6. invalidation-watermark freshness enforcement;
7. sandbox/hypervisor and egress-enforcement boundaries;
8. high-risk effect reconciliation;
9. authority-ledger integrity and independent checkpoint witnessing;
10. the protected software-supply-chain path that updates those components;
11. certificate-context resolution, evidence-applicability checks, and the authority path that decides whether a successor certificate exists;
12. pack/spine composition-manifest validation, interaction-graph resolution, and the authority path that decides whether modular credit or an interaction certificate is sufficient.

Everything else is outside the security TCB.

This separation is more aggressive than a conventional agent platform and is the main reason the architecture scales safely to heterogeneous models.

```mermaid
flowchart TB
    U[Users / applications / domain APIs]

    subgraph UNTRUSTED["UNTRUSTED INTELLIGENCE & EXECUTION PLANE"]
        ORCH[Orchestrator / planners / producers]
        MR[Semantic Model Router<br/>Switchyard-style]
        FAPI[Frontier APIs]
        NIM[Nemotron / NIM]
        OWM[Local open-weight models]
        VER[Verifier models / breakers]
        CELL[Isolated compute cells]
    end

    subgraph TCB["SECURITY TCB"]
        ID[SPIFFE / SPIRE<br/>workload identity]
        POL[Policy Composer + OPA<br/>signed policy bundles]
        KEY[KMS / HSM / Vault<br/>signing + secrets]
        MON[Authorization Monitors<br/>Certification / Release / Memory]
        BROKER[Runtime Tool Broker<br/>grant verifier]
        EFF[PostgreSQL<br/>effect slots + operation records]
        INV[Durable invalidation stream<br/>monotonic watermark]
        REC[Effect observer / reconciler]
        ISO[Sandbox + network enforcement<br/>Kata / microVM / gVisor boundary]
        LEDGER[Signed authority ledger<br/>checkpoint verifier]
    end

    subgraph DATA["DATA & AVAILABILITY SERVICES"]
        ART[Content-addressed<br/>S3 / Ceph artifacts]
        WF[Temporal workflows]
        OTEL[OpenTelemetry]
        WORM[Independent WORM witness]
    end

    subgraph FACTORY["MODEL FACTORY — UNTRUSTED UNTIL PROMOTION"]
        TRACE[Authenticated trace intake]
        CUR[Privacy + curation<br/>NeMo Curator / custom]
        LAB[Oracle / human label join]
        TRAIN[Router / specialist / verifier training]
        EVAL[Independent evaluation]
        REG[Candidate registry]
    end

    EXT[External authoritative systems<br/>GitHub / email / DB / deployment / cloud APIs]

    U --> ORCH
    ORCH --> MR
    MR --> FAPI
    MR --> NIM
    MR --> OWM
    ORCH --> CELL
    VER --> ORCH

    ID --> POL
    ID --> BROKER
    KEY --> MON
    KEY --> BROKER
    POL --> MON
    POL --> BROKER
    INV --> MON
    INV --> BROKER
    MON --> BROKER
    BROKER --> EFF
    BROKER --> REC
    BROKER --> EXT
    ISO --> CELL
    EFF --> LEDGER
    MON --> LEDGER
    LEDGER --> WORM

    WF --> ORCH
    ART --> ORCH
    ART --> VER
    ORCH --> OTEL
    BROKER --> OTEL

    ORCH --> TRACE
    BROKER --> TRACE
    VER --> TRACE
    TRACE --> CUR
    CUR --> LAB
    LAB --> TRAIN
    TRAIN --> EVAL
    EVAL --> REG
    REG -. "candidate only; governed promotion" .-> MR
    REG -. "candidate only; governed promotion" .-> NIM
```

NVIDIA is especially strong in the **untrusted execution and Model Factory portions**: NIM for packaged inference, Dynamo for GPU-serving routing, Switchyard for semantic model routing, GPU Operator for accelerator management, NeMo Curator for data preparation, Data Designer for synthetic data, and NeMo RL/Gym for post-training and distillation. Switchyard is now explicitly positioned as inference middleware for routing a virtual model across stronger and weaker backends. citeturn28search16 KServe independently offers a vendor-neutral Kubernetes serving path; its LLMInferenceService reached production-ready status in v0.17 with KV-aware routing, distributed inference and disaggregated prefill/decode, and the current documentation has advanced LLM serving as a first-class path. citeturn28search2turn28search15

The Model Factory should be **self-improving but never self-authorizing**. Production traces can automatically create datasets, train routers, distill specialists, train verifiers, run evaluations and propose new model bundles. They must not automatically confer production authority on their descendants. Promotion remains a governed transition evaluated against the Reusable Core's invariant hierarchy and certified risk/coverage requirements. That is a direct application of the Core rather than an additional restriction. fileciteturn0file0

The economic flywheel should be:

```text
frontier models solve difficult/new cases
        ↓
authenticated traces + objective outcomes
        ↓
curation + provenance + independent labeling
        ↓
find repeated, learnable task slices
        ↓
distill specialists / train routers / train verifiers
        ↓
shadow + canary + certified evaluation
        ↓
move qualified traffic downward in cost
        ↓
frontier models concentrate on the remaining hard tail
```

The pack/spine assurance layer is valid only when **independent certification is not mistaken for compositional sufficiency**. The complementary composition property is:

```text
independently certified components
    !=> compositionally sufficient configuration

maximum modular reuse
    -> discharge dependency assumptions
    -> prove state stability / mediation
    -> bound composed authority
    -> account for evidence dependence
    -> establish global properties
    -> remain inside every usage domain
```

Unresolved interaction edges determine the additional certification scope; they do not automatically force whole-system recertification.

The certificate system is valid only while authority is bound to the **exact context that was certified**. The complementary durability property is:

```text
changed certified context
    -> old certificate cannot authorize

but

changed certified context
    !=> erase all prior assurance evidence

invalidate exactly
    -> compute affected claims and interactions
    -> preserve only still-applicable evidence
    -> acquire minimum sufficient delta evidence
    -> issue successor certificate
```

This avoids both stale authority and the opposite failure mode in which every harmless change triggers a full-system recertification.

The flywheel is valid only while it remains coupled to an **external epistemic reference process**. The complementary stability property is:

```text
recursive intelligence != recursive truth

internal agreement, evaluator pass rate, and specialist substitution
do not by themselves establish improvement

fresh independently grounded evidence must remain causally
distinguishable from the portfolio's own descendants
```

This is broader than recursive synthetic-data collapse. The router changes which observations are collected; the verifier changes which observations are labeled successful; specialists change the future production distribution; and verifier successors can inherit ancestral criteria. The entire portfolio can therefore become self-confirming while every authority transition remains valid.

This extends the model-routing architecture in the preceding Nemotron report. That report correctly separated agent-stage routing, model routing and inference-instance routing; the architecture here adds the **trusted substrate below those mechanisms and the governed learning loop around them**. fileciteturn0file1

There is **no fundamental contradiction in Reusable Core v1.9 that prevents concrete implementation**. There are, however, six important implementation consequences:

| Core requirement | Concrete consequence |
|---|---|
| Immutable authority record | A normal database table is not enough. Use append-only permissions, cryptographic chaining/signatures and independently witnessed WORM checkpoints. |
| At-most-one authoritative semantic effect | Do not promise universal distributed “exactly once.” Reserve semantic effect slots transactionally and reconcile unknown provider outcomes. The Core already makes this distinction. |
| Current global invalidation state | In a WAN partition, strict freshness and full availability cannot both be preserved. The correct implementation is home-region authority plus fail-closed behavior or an explicit epoch-transfer protocol. |
| Credentials never exposed to agents | Sandboxes that merely inject API keys as environment variables do **not** satisfy this invariant. Credentials must remain behind broker/inference proxies. |
| Independently certified packs/spines do not automatically compose | Require signed composition manifests, typed interaction closure, and `COMP-L0…L3` scoping before modular credit is used. Unresolved interactions receive the minimum sufficient interaction-specific certification rather than automatic whole-system trust. |
| Certificate authority is exact-context | Any CCH mismatch makes the predecessor certificate non-authorizing. Preserve only still-applicable evidence and issue a successor certificate for the changed configuration. |

The rest of this report specifies that architecture.

## Normative architecture and trust model

The mistake to avoid is interpreting “trusted runtime” as “everything deployed inside our Kubernetes cluster.” Kubernetes itself is far too large, and the AI serving stack changes far too rapidly, for that to be a useful security boundary.

The right distinction is between **security TCB**, **availability dependencies**, and **untrusted intelligence**.

| Class | Compromise means | Examples |
|---|---|---|
| **Security TCB** | Could produce an unauthorized authoritative transition or falsify its authorization state | identity roots, broker, policy enforcement, monitor signing, effect-slot state, sandbox boundary |
| **Availability/liveness dependency** | Could halt, duplicate scheduling, delay or lose work, but cannot independently authorize effects | Temporal, most queues, model serving |
| **Epistemically untrusted** | Could produce wrong/malicious candidates or judgments | LLMs, router models, verifier models, retrieved content |
| **Diagnostic only** | Could obscure monitoring but cannot become evidence by itself | dashboards, generic traces, cost telemetry |

The Core's own component model already puts the Runtime Tool Broker in the TCB while treating routers, producers and telemetry learners as different authorities. fileciteturn0file0

**SPIFFE/SPIRE should be the cross-platform workload identity layer.** An X.509-SVID gives a workload a short-lived cryptographic identity suitable for mTLS, while SPIFFE explicitly prefers X.509-SVIDs where possible over JWT-SVID bearer tokens because bearer tokens introduce replay concerns. citeturn15search8turn15search9 In cloud clusters, native workload identities remain useful at the cloud-resource edge: GKE Workload Identity Federation, EKS Pod Identity and AKS Workload Identity bind Kubernetes identities into each provider's IAM system. citeturn13search7turn14search1turn14search0

The resulting identity chain should be:

```text
Core principal
    ↓
SPIFFE workload identity
    ↓
mTLS to broker / monitor
    ↓
broker verifies requested principal == authenticated principal
    ↓
when needed:
SPIFFE identity → cloud workload identity → narrowly scoped cloud credential
```

A model-generated field such as:

```json
{"principal": "release-controller"}
```

carries **zero authority**. The effective principal is determined from the authenticated channel.

**Secrets and signing keys should live outside agent processes.** Vault supports dynamic credentials, cryptographic transit operations and centralized secret lifecycle management; managed cloud KMS/HSM services can substitute at production scale. citeturn13search1turn13search5turn13search12 I recommend that Authorization Monitor signing keys be separate from ordinary application secrets and, at higher assurance levels, HSM/KMS-backed so the raw private key is not exportable.

**OPA is the best fit for runtime policy evaluation, but not for the Core's entire policy semantics.** OPA supports cryptographically verified policy bundles and emits rich decision records. citeturn15search0turn15search4 The Reusable Core's monotonic policy-composition algebra should therefore be implemented as a small typed library that produces the normalized `EffectivePolicy`; OPA consumes that normalized policy and evaluates concrete authorization decisions. This keeps subtle composition rules out of ad hoc Rego snippets.

The sequence is:

```text
core policy
deployment policy
domain-pack policy
tenant policy
task policy
incident overrides
       ↓
typed monotonic policy composer
       ↓
EffectivePolicy + digest + non-expansion proof
       ↓
signed OPA bundle / decision inputs
       ↓
allow / deny / human-required / unsupported
```

A router cannot change this pipeline.


### Compositional assurance across Core spines and domain packs

The runtime needs one additional assurance boundary that sits **above individual pack certification but below reflexive whole-system recertification**.

A signed domain-pack certificate is not by itself evidence that the configured composition is safe. The runtime therefore maintains a `PackCompositionManifest` for every Core spine, domain pack, and shared service participating in a governed configuration.

The manifest declares:

```text
assumptions / imported guarantees
exported guarantees
state read/write footprint
authority and delegation surface
evidence provenance families
usage/configuration envelope
policy-combination operator
global-property / hyperproperty class
certificate references
```

The composition registry compiles these declarations into a typed interaction hypergraph:

$$
\mathcal G=
(V,E_D,E_S,E_A,E_E,E_H).
$$

The interaction classes are:

```text
E_D  dependency / assume-guarantee edges
E_S  shared-state edges
E_A  authority-overlap / delegation edges
E_E  evidence/common-cause edges
E_H  global-property / hyperproperty edges
```

Hyperedges may involve more than two components. This matters because some authority, state, or policy interactions arise only in three-pack or pack+spine combinations and are invisible to pairwise checks.

A configured composition receives maximum modular reuse only when:

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

The runtime interpretation is deliberately narrow:

```text
ReuseEligible
    =
no new unresolved interaction-specific proof obligation

ReuseEligible
    !=
all integration/acceptance activity is waived
```

An applicable standard, regulator, or deployment policy may still require integration acceptance.

#### Dependency closure

For every component $i$,

$$
Env\land
\bigwedge_{j\in Pred(i)}G_j
\models A_i.
$$

Use the whole predecessor set because several guarantees may jointly establish one assumption.

Cycles are not automatically forbidden, but a cyclic dependency requires an explicit well-founded/circular-reasoning artifact. A cycle without that artifact is an interaction trigger.

#### State sharing

A simple static detector can identify potential interference with read/write incidence matrices $R,W$:

$$
X_S=WR^\top+WW^\top.
$$

A nonzero entry means **review this interaction**, not **unsafe**.

For a relied-upon invariant $I_i$ and foreign transition $T_j$, the substantive proof is:

$$
I_i(s)\land T_j(s,s')
\Rightarrow I_i(s').
$$

Disjoint footprints can be discharged mechanically. Shared mutation must be covered by ownership, serialization, or invariant-stability evidence.

Append-only/content-addressed state reduces destructive mutation but does not by itself establish semantic noninterference. New facts can still change authorization, revocation, resource, temporal, or rule-selection semantics.

#### Authority overlap

The composed authority closure must stay inside the certified ceiling:

$$
Cl\left(\bigcup_iU_i\right)\subseteq U_{\max}.
$$

General authority-leakage reachability is not exactly decidable for arbitrarily expressive protection systems. The registry therefore uses either:

```text
restricted exact authority model
OR
sound conservative over-approximation
```

and accepts only when the exact/over-approximated reachable authority remains below the ceiling.

A simple overlap score may prioritize review but cannot certify safety. One shared `release.publish` capability can matter more than hundreds of shared read-only capabilities.

Order-sensitive policy combinators also create a composition dependency. If:

$$
P_i\otimes P_j\ne P_j\otimes P_i,
$$

pack load/order is frozen into the certified configuration.

#### Evidence sharing

The runtime MUST NOT require blanket statistical independence of certificates. It MUST require that material dependence is represented consistently with the confidence claim.

The practical ladder is:

```text
E0  structural provenance overlap
E1  causal/common-cause model
E2  calibrated quantitative dependence model where data justify it
```

Shared verifier, corpus, simulator, base model, specification, assessor, or oracle family is recorded. It is never silently treated as independent corroboration.

For probabilistic claims with unknown dependence, conservative bounds may be sufficient. With marginals $p_A,p_B$:

$$
\max(0,p_A+p_B-1)
\le
P(A\cap B)
\le
\min(p_A,p_B).
$$

If the worst-case bound already satisfies the required system claim, the composition does not need a more elaborate joint model solely for that reason.

#### Global properties and hyperproperties

Local guarantees must establish the actual global claim:

$$
\bigwedge_iG_i\models Q
$$

either directly or through a named composition theorem whose side conditions are checked.

Noninterference and other hyperproperties default to interaction-aware certification unless an applicable theorem discharges the exact relational property. Local trace correctness is not enough.

#### Usage-domain validity

Every configured pack must remain inside the assumptions/configuration envelope under which its certificate was issued:

$$
\theta_{\mathrm{actual}}\in\Theta_i.
$$

A byte-identical reused pack outside its declared usage domain loses the relevant modular credit.

#### Runtime trigger predicate and certification levels

The registry emits an unresolved interaction whenever any of these holds:

```text
shared mutable state without frame/invariant/serialization evidence
dependency cycle without sound discharge
undischarged assumption
possible authority ceiling/tier crossing
ambient shared credential or tool authority
material evidence dependence ignored
unsupported probabilistic joint claim
order-sensitive policy composition with unfrozen order
unproved global hyperproperty
usage-domain escape
composition theorem used outside setup/state/concurrency assumptions
```

The runtime assigns:

```text
COMP-L0  modular reuse + compatibility validation
COMP-L1  local/pairwise interaction certificate
COMP-L2  declared-configuration integration certificate
COMP-L3  end-to-end joint recertification
```

The unit of additional assurance is the unresolved interaction hyperedge, not automatically the entire system.

Let $U$ be the uncovered interaction set. The desired operational condition is:

$$
U=\varnothing
$$

for `COMP-L0`, or else every $e\in U$ must be covered by an `InteractionCertificate` whose scope and level are sufficient for that edge before configuration activation.

A later implementation may optimize certification scopes as a weighted set-cover problem. The initial implementation can conservatively compute connected interaction closures. The important invariant is that scope is **traceable to the interaction graph**, not silently guessed.

A minimal interaction manifest can be represented as:

```yaml
composition:
  component_id: "domain-pack-medical"
  version: "2.1.0"
  artifact_digest: "sha256:..."
  composition_manifest_digest: "sha256:..."
  certified_context_hash: "sha256:..."
  assumptions:
    - from: "core.authz"
      id: "A_authz"
  guarantees:
    - id: "G_phi_redaction"
      type: "safety"
  state:
    reads: ["core.fact_store"]
    writes: ["core.fact_store"]
    access_mode: "append_only"
    invariant_refs: ["proof:fact-monotone-17"]
  authority:
    capabilities: ["tool.db.read", "tool.email.send"]
    authority_ceiling: "tier-2"
    ambient: false
    analysis_model: "conservative_overapprox"
  evidence:
    provenance_families:
      - "verifier-X@3.2"
      - "corpus:blake3:9f2c..."
      - "sim-Y@1.4"
  usage_domain:
    conditions: ["input_lang=en", "max_tools<=8"]
  policy:
    combinator: "deny-overrides"
    load_order_fixed: true
  global_properties:
    - id: "H_confidentiality"
      class: "hyperproperty"
      composition_rule_ref: "MAKS-profile-2"
```

This registry object is assurance metadata. It does not mint runtime authority.




#### Relationship to RQ18 certificate durability

`COMP-L*` and `CERT-D*` are orthogonal controls:

```text
COMP-L*
    = required assurance scope for the configured composition

CERT-D*
    = strategy for restoring that assurance after the configuration changes
```

The runtime SHOULD use one typed assurance graph for both. RQ17 evaluates the graph horizontally across packs/spines; RQ18 uses the same dependency and interaction structure temporally to determine which claims, evidence records, and interaction certificates are affected by a mutation.

Every `InteractionCertificate` that contributes to activation MUST bind to the exact successor `CertifiedContextHash` or equivalent exact configuration identity. A changed context therefore supersedes the prior interaction certificate for authority even when its underlying proof/evidence can be carried into the successor process.

The Core's `AuthorityGrant` should be implemented as a **signed, single-use, principal-bound capability statement rather than a bearer API token**. A representative wire object is:

```json
{
  "grant_id": "g_...",
  "issuer": "spiffe://core/monitor/effects",
  "audience": "spiffe://core/runtime-broker",
  "principal": "spiffe://core/worker/run-7/producer-2",
  "run_id": "run-7",
  "action_id": "github.create_pull_request",
  "action_version": "4",
  "implementation_digest": "sha256:...",
  "resource_handles": ["repository:abc123"],
  "parameter_digest": "sha256:...",
  "effective_policy_digest": "sha256:...",
  "effect_slot": "slot:run-7:publish-1",
  "operation_id": "op:...",
  "max_uses": 1,
  "lease_epoch": 183,
  "invalidation_watermark": 7349921,
  "not_before": "...",
  "expires_at": "..."
}
```

The broker validates both the signature **and** the authenticated SPIFFE identity against `principal`, so theft of the serialized grant does not by itself make it usable.

The most important trust boundary is consequently:

```mermaid
sequenceDiagram
    participant M as Untrusted model / agent
    participant W as Workflow worker
    participant P as Policy / Monitor TCB
    participant D as Effect DB
    participant I as Invalidation Bus
    participant B as Runtime Broker
    participant X as External Provider
    participant R as Independent Reconciler
    participant L as Authority Ledger

    M->>W: Propose typed semantic action
    W->>P: Request authority
    P->>I: Read current watermark
    P->>P: Validate policy, principal,<br/>subject/resource digests
    P->>D: Reserve semantic effect slot
    D-->>P: slot + lease epoch
    P-->>B: Signed one-use grant

    B->>I: Recheck current watermark
    B->>D: Recheck slot, operation,<br/>lease and request digest

    alt Preconditions still valid
        B->>X: Perform operation<br/>with broker-owned credential
        alt Provider returns authoritative receipt
            X-->>B: receipt/result
            B->>D: mark operation committed
        else Result ambiguous / timeout
            B->>D: outcome_unknown
            B->>R: reconcile, do not blind-retry
            R->>X: query receipt/state
            R-->>D: committed / definitely absent / unresolved
        end
        D->>L: Append terminal authority record
    else stale or invalid
        B-->>W: fail closed
    end
```

For external effects, PostgreSQL is a particularly good fit for the authoritative transactional state because its `SERIALIZABLE` isolation level makes successfully committed concurrent transactions equivalent to a serial ordering, while correctly requiring applications to retry serialization failures. citeturn11search0 That does not make external APIs transactional. It makes the **right to attempt an effect** and its semantic cardinality transactional.

A practical table set is:

```text
authority_records
effect_slots
operations
leases
effective_policies
invalidation_observed
certificates
artifact_subjects
evidence_refs
principal_epochs
```

For an effect:

```text
effect_slot:
  slot_id
  semantic_intent_digest
  max_commits
  committed_count
  owner_principal
  lease_epoch
  state

operation:
  operation_id
  slot_id
  request_digest
  state = reserved|in_flight|committed|definitely_absent|outcome_unknown
  provider_idempotency_key
  provider_receipt
```

The invariant is:

$$
N_{\text{authoritative commits}}(h)\le m(h)
$$

rather than the impossible blanket statement “all external side effects execute exactly once.”

Temporal is recommended above this layer for durable workflow execution. Temporal's durable-execution model can resume workflows after process or infrastructure failures, and its model requires nondeterministic I/O such as model calls and tool calls to occur through Activities rather than replayed workflow logic. citeturn12search6turn12search12 That is an excellent fit for the Core—but **Temporal retries must never constitute the idempotency mechanism for consequential effects**. Retried Activities simply re-enter the broker, which joins or reconciles the already-reserved effect slot.

That distinction lets Temporal remain outside the security TCB.

## Trusted runtime and execution substrate

The runtime should be divided into **control services, arbitrary compute, model inference, authoritative effects, and diagnostic telemetry** rather than treating every workload as another pod with the same privileges.

The recommended implementation is:

```text
Application/API
    │
    ▼
Temporal workflow
    │
    ├── Producer Activity ──→ ModelRouter ──→ Switchyard
    │                               │
    │              ┌────────────────┼─────────────────┐
    │              ▼                ▼                 ▼
    │           frontier         NIM/Nemotron       KServe/vLLM
    │                               │                 │
    │                            Dynamo       generic serving
    │
    ├── Verification Activity ──→ deterministic gates / verifier models
    │
    ├── Isolated Compute Activity ──→ Kata/gVisor/microVM
    │
    └── Effect Activity
             │
             ▼
        Runtime Broker
             │
       grant + policy +
       effect slot check
             │
             ▼
       external service
```

**Semantic model routing and physical inference routing must remain separate.** Switchyard addresses the former: NVIDIA currently describes it as inference middleware supporting virtual models that route requests among stronger and weaker backends. citeturn28search16 NIM provides NVIDIA-optimized packaged inference; NIM Operator manages NIM deployment lifecycle and Kubernetes integration. Dynamo belongs lower still, where model requests are dispatched among self-hosted inference workers based on serving-state concerns such as KV-cache locality and load. The prior routed-agent analysis reached the same separation. fileciteturn0file1

A stable internal interface should hide all of those products:

```python
class ModelEndpoint:
    semantic_id: str
    provider: str
    model_version: str
    capabilities: set[str]
    privacy_classes: set[str]
    supported_regions: set[str]
    max_context_tokens: int
    supports_tools: bool
    supports_structured_output: bool
    current_health: str
    pricing_snapshot_id: str
    validation_snapshot_id: str

class ModelRouter:
    async def route(
        self,
        request,
        effective_policy,
        workflow_stage,
        evidence_state,
    ) -> "RouteDecision":
        ...
```

The route result is a **proposal**, not an authority grant.

Switchyard can implement `ModelRouter` today, but application code should not depend directly on its internal configuration schema. That preserves the ability to replace it with an in-house router, a future NVIDIA implementation, or another gateway without changing Core semantics.

**KServe is the most attractive vendor-neutral Kubernetes alternative.** KServe 0.17 declared its LLMInferenceService production-ready with KV-cache-aware routing, distributed inference and disaggregated prefill/decode; current KServe documentation distinguishes a simpler standard LLM path from the advanced LLMInferenceService path. citeturn28search2turn28search15 Use KServe/vLLM when model portability is more important than NVIDIA-specific optimizations; use NIM/Dynamo when NVIDIA hardware optimization and NIM packaging materially improve your measured workload.

**NIM Operator's DRA integration should not yet be a production dependency.** NVIDIA's current documentation explicitly labels DRA support in NIM Operator as Technology Preview and unsuitable for production, despite the underlying Kubernetes DRA ecosystem having matured substantially. citeturn28search0turn28search1 For production NIM today, use established full-GPU/MIG allocation paths and treat NIM+DRA as a later migration candidate.

GPU scheduling must also distinguish **efficiency from isolation**. NVIDIA's Kubernetes GPU time-slicing documentation states explicitly that time-sliced replicas do not receive the memory or fault isolation provided by MIG. citeturn28search4 NVIDIA's current vGPU documentation describes stronger hardware isolation for MIG-backed configurations. citeturn28search5turn28search6 Consequently:

```text
same-trust batch inference:
    time-slicing may be acceptable

separate application tenants:
    MIG or stronger isolation

hostile arbitrary GPU code:
    dedicated GPU VM/node is preferred

authority-bearing services:
    should not share a trust boundary with untrusted GPU workloads
```

For CPU arbitrary code execution, the security tiers should be:

| Workload | Runtime |
|---|---|
| Trusted deterministic service | ordinary hardened container |
| Low/medium-risk generated code | gVisor or equivalent syscall-interposition sandbox |
| High-risk untrusted code | Kata Containers / microVM-grade isolation |
| Extremely sensitive or hostile workload | ephemeral dedicated VM plus brokered network |
| GPU-hostile workload | dedicated GPU VM/node rather than assuming a container boundary is sufficient |

gVisor places a user-space application kernel between sandboxed applications and the host Linux kernel; Kata instead runs container workloads inside lightweight VMs with an additional hardware-virtualization boundary. Firecracker provides a similarly small KVM-based microVM model. citeturn3search0turn3search1turn3search5

NVIDIA OpenShell is interesting as a developer-oriented option. It combines network mediation with OPA, filesystem controls and process restrictions, and its inference gateway can keep model-provider credentials out of the sandbox's direct request path. citeturn9search7turn8search6 But it should not be made a hard dependency of the Core yet: NVIDIA currently presents OpenShell as an early/alpha system, and some credential-injection modes expose provider credentials to the sandbox process environment rather than satisfying the Core's stronger “agent never receives credentials” requirement. citeturn9search0

The correct integration is therefore:

```text
OpenShell/gVisor/Kata
      =
execution containment

Runtime Broker
      =
authority containment

These are complementary, not substitutes.
```

**Network access from arbitrary compute cells should default to deny.** Retrieval or API access needed by generated code should use explicit mediated read actions or a policy proxy. No compute cell should possess the network path plus credential necessary to mutate authoritative state.

For invalidation, use a dedicated durable stream with a monotonically increasing authoritative offset. NATS JetStream is an attractive implementation because replicated streams use Raft and provide strongly ordered stream semantics; Kafka is equally viable where it is already the enterprise standard, with ordering scoped naturally to a partition. citeturn16search1turn16search14 I recommend **one logically dedicated invalidation stream** rather than mixing invalidations with high-volume telemetry.

Each monitor persists:

```text
last_seen_invalidation_sequence
last_confirmed_global_high_watermark
decision_sequence
decision_time
```

and refuses a governed transition if it cannot establish that its view is current enough under policy.

That requirement has an unavoidable distributed-systems consequence:

> **During a network partition, the architecture chooses authority correctness over availability.**

In hybrid multi-cloud operation, the cleanest implementation is to assign each authoritative run or effect domain a **home authority region and epoch**. Only that region may commit. Failover requires an explicit epoch transfer after establishing that the old writer can no longer commit. Attempting casual active-active authority writes across a partition would violate the Core's exact-object/freshness discipline.

Artifacts should be **content-addressed**:

```text
artifact_id = SHA-256(canonical_bytes)
```

with metadata stored separately. Cloud deployments should use object storage with retention/WORM for witnesses; private clusters can use Ceph RGW. Rook provides Kubernetes operation of Ceph/RGW, and Ceph supports S3-compatible Object Lock. citeturn18search8turn18search0 New deployments should not build around the former MinIO Community repository: the open repository was archived in April 2026 and is read-only. citeturn17search0turn17search11

The object store does **not** need to be trusted for artifact integrity provided every artifact is verified against its expected digest before use. It remains an availability dependency.

The authority ledger has stronger requirements. I recommend:

```text
PostgreSQL append-only authority records
        +
per-monitor hash chain
        +
per-monitor signature
        +
periodic independently signed checkpoint
        +
checkpoint copy in Object-Lock/WORM storage
```

Conceptually:

$$
h_i=H(h_{i-1}\parallel \operatorname{canonical}(record_i))
$$

and the monitor signs $h_i$ with its dedicated key. A separate witness signs/checkpoints high-water marks; the monitor cannot witness itself.

Sigstore/in-toto-style signed attestations are useful for software, model and dataset provenance so that the build/train/release chain can verify which source, dataset and environment produced an artifact. Sigstore's signing and transparency mechanisms are designed around signed software artifacts and attestations; SLSA-style provenance supplies the broader build-lineage model. citeturn6search2turn6search12turn25search12

Finally, **OpenTelemetry is diagnostic transport, not an authority ledger**. NeMo Agent Toolkit also exposes OpenTelemetry-compatible observability paths. citeturn7search1turn7search9 A compromised OTel collector must not be able to fabricate a verified artifact or authorized effect.

Use two paths:

```text
ordinary operational telemetry
    → OpenTelemetry
    → metrics / traces / logs / ClickHouse

authority-relevant evidence
    → authenticated evidence-ingest service
    → digest/signature validation
    → authority/evidence database
    → referenced from OTel by ID
```

That distinction closes a subtle but important trust gap.


## Certification durability under drift and change

The trusted runtime needs a stricter certificate lifecycle than a conventional "certificate valid until date X" model.

The primary object is an exact, content-addressed **Certified Context Hash (`CCH`)** over the assurance-relevant closure. A certificate issued for context $x$ cannot authorize a different context $x'$:

$$
H(x')\neq H(x)
\Rightarrow
C_x\not\vdash Authorization(x').
$$

That hard rule should not be weakened by a semantic-similarity score. Instead, semantic similarity controls the **cost of issuing the successor certificate**, not whether the predecessor continues to authorize.

### What the CCH binds

For each certificate, resolve the canonical closure from the currently active identities and contracts:

```text
resolved model identity / digest / served version
prompt and system-prompt digests
tool implementation + interface-contract digests
schema/data-contract versions
effective policy + authorization/harm-hierarchy version
reference/evaluation protocol
judge model + prompt where applicable
canonicalization/runtime profile where claim-relevant
dependency-certificate CCHs
operating-envelope identifier
behavioral-probe specification identity
```

A Merkle-style construction lets one dependency update change all downstream certificate context identities without ad hoc invalidation code.

The authority database should persist both the certificate's `cch` and the dependency IDs/digests that produced it. The invalidation outbox then records exact affected subjects and certificate scopes.

### Certificate identity is not evidence identity

The key distinction is:

```text
old certificate changed-context authority = none

but

old evidence applicability = evaluated item by item
```

A changed prompt hash, model identity, tool implementation, or reference protocol supersedes the old certificate. The successor process can still reuse a deterministic proof or independent evaluation whose assumptions are demonstrably unaffected.

That gives the runtime an incremental path:

```text
context mutation
    ↓
old CCH mismatch
    ↓
predecessor certificate -> SUPERSEDED / SUSPENDED
    ↓
CertificationClosurePlus
    ↓
evidence-applicability resolution
    ↓
cheap differential screen
    ↓
scoped delta verification
    ↓
interaction verification where required
    ↓
full recertification only if needed
    ↓
new certificate with new CCH
```

This is the certification analogue of content-addressed build invalidation plus incremental verification.

### Certificate states

Use at least:

```text
VALID
RESTRICTED
SUSPENDED
REVOKED
SUPERSEDED
```

`SUPERSEDED` is important: the certificate can remain a valid historical statement that configuration $x$ passed its requirements while carrying zero authority for configuration $x'$.

### `CertificationClosurePlus`

A plain transitive dependency DAG is not sufficient for agentic systems because claims can depend on combinations such as:

$$
\{model,prompt,tool\}\rightarrow q.
$$

The closure engine should therefore operate over typed assurance dependencies:

```text
causal
assumption
evidence
reference
composition
authority
interaction
```

Conceptually:

$$
CertificationClosure^+(\delta)
=
DependencyClosure(\delta)
\cup
InteractionClosure(\delta).
$$

The interaction term matters when two changes that are benign alone become unsafe together. A model upgrade and prompt rewrite, for example, may each pass component-local tests yet change tool-selection behavior jointly.

The first implementation can conservatively encode known interaction edges and fall back to full recertification when interaction structure is unresolved. More advanced Sobol/Shapley/factorial interaction estimates belong in the RQ18 research program until validated.

### Evidence applicability

Authority-relevant evidence should include enough metadata to decide whether it survives a context change:

```text
evidence_id
claim_ids
dependency_digests
assumption_refs
reference_protocol_digest
operating_envelope_ref
evidence_family_ids
common_cause_group_ids
freshness_contract
invariance_proof_refs
source_certificate_ids
```

Evidence is reusable only if its assumptions remain true and the changed dependencies are outside its applicability surface or are covered by a validated invariance proof.

This also prevents a subtle assurance inflation failure: three verifier outputs based on one contaminated benchmark are three records, but not necessarily three independent evidence families.

### Hidden provider and environmental drift

Content addressing only handles state the runtime can identify. API-served models can change behind stable aliases, and workload distributions can drift without any artifact mutation.

Use three layers:

```text
1. deterministic observable dependency change
       -> CCH invalidation

2. stochastic observable behavioral change
       -> sentinel / fingerprint / production monitor

3. residual unobservable state
       -> TTL backstop
```

The behavioral monitor should hash its **protocol**, not individual random outputs:

```text
sentinel set version
decoding/sampling protocol
representation
distance statistic
reference baseline
monitor algorithm/version
decision threshold
```

A live model is then tested against the behavioral envelope.

For permanent monitoring, fixed-sample hypothesis tests repeatedly peeked over time are unsafe because false alarms accumulate. Where the monitor supports an ongoing assurance claim, use an anytime-valid design such as a confidence sequence, e-process/test martingale, or another procedure with an explicit stopping-time guarantee under the declared sampling assumptions.

TTL is retained only for the residue that cannot be reliably observed. A known CCH mismatch is never "allowed until TTL expires."

### Semantic distance and robustness margin

The runtime should not hard-code a universal notion of "small change." RQ18 may validate claim-specific semantic distances:

$$
d_q(x,x')
$$

and assurance margins:

$$
g_q(x)
=
ObservedAssurance_q(x)-RequiredAssurance_q.
$$

If a validated sensitivity relation exists,

$$
|g_q(x')-g_q(x)|
\le
L_qd_q(x,x'),
$$

then a sufficient local carry-forward condition is:

$$
d_q(x,x')
<
\frac{g_q(x)}{L_q}.
$$

Operationally, that would mean "cheap successor proof permitted," not "old certificate remains valid."

Until such bounds are empirically calibrated, the production runtime should use explicit change classes plus scoped differential verification.

### Predeclared change envelopes

For recurring safe modification classes, the system may register a `ChangeEnvelope`:

```text
change class
eligible component/claim classes
assumptions
allowed semantic bounds
required screen
required delta gates
interaction obligations
abort/escalation conditions
cumulative-change budget / invariant-region rule
```

This is the runtime analogue of a predetermined change-control plan.

A change inside the envelope still receives a new CCH and successor certificate. The envelope only shortens the proof.

Cumulative safety matters: individually allowed changes can compose into an unsupported state. The runtime therefore needs either a cumulative budget or an invariant-region check before repeatedly applying the fast path.

### Minimum-evidence recertification

Start with a transparent cascade:

```text
CCH mismatch
  -> resolve exact changed dependencies
  -> calculate CertificationClosurePlus
  -> retain still-applicable evidence
  -> cheap discriminator / sentinel / contract check
  -> scoped delta gates
  -> joint interaction gates where declared
  -> full recertification if unresolved
```

The research-level optimization is:

$$
T^\star
=
\arg\min_T Cost(T)
$$

subject to every affected claim returning to its risk bound.

A weighted set-cover or value-of-information controller may reduce the number of gates and samples. A POMDP can model hidden certificate validity and trade verification cost against stale-authority risk. Those are later optimizations; the first production implementation should remain transparent and auditable.

### Stale-authority risk

The primary failure metric is:

$$
R_{\mathrm{stale}}
=
P(
\text{authority active}
\land
\text{prerequisite claim false}
).
$$

Harm tiers should allocate different risk budgets. This naturally makes high-harm certificates more conservative under opaque providers and weak monitoring.

A simple hidden-change hazard model can help size a TTL, but no exponential-hazard assumption should be constitutionalized. TTL is estimated from actual provider/change history, monitoring power, and consequence budgets.

### Authority degradation

Certificate loss should remove the permission that depended on the stale claim rather than necessarily shutting down unrelated capabilities.

Order authority sets by inclusion:

$$
A_1\preceq A_2
\iff
A_1\subseteq A_2.
$$

The live authority resolver returns only permissions whose prerequisite claims remain currently supported.

Required invariant:

$$
Q'_{\mathrm{valid}}\subseteq Q_{\mathrm{valid}}
\Rightarrow
Authority(Q'_{\mathrm{valid}})
\preceq
Authority(Q_{\mathrm{valid}}).
$$

Uncertainty can reduce authority. It can never increase it.

### Suggested persistence model

Add or extend authority-plane objects:

```text
certified_contexts
    context_id
    cch
    component_manifest_ref
    operating_envelope_ref
    behavioral_probe_spec_ref
    opaque_dependency_refs
    created_at

certificates
    certificate_id
    state
    subject_digest
    cch
    claim_set_digest
    authority_set_digest
    freshness_contract_ref
    predecessor_certificate_id
    issued_at
    expires_at
    signature_ref

evidence_applicability
    evidence_id
    claim_ids
    dependency_digests
    assumption_refs
    reference_protocol_digest
    evidence_family_ids
    common_cause_group_ids
    freshness_contract_ref
    invariance_proof_refs

certification_change_assessments
    predecessor_cch
    successor_cch
    changed_dependencies
    dependency_closure_claims
    interaction_closure_claims
    retained_evidence
    invalidated_evidence
    delta_obligations
    change_envelope_ref
    hidden_drift_status
    full_recert_required
```

### Runtime metrics

Add:

```text
certificate CCH mismatch count
stale-certificate authorization attempts
invalidation precision / recall on seeded changes
certified-context coverage
time-to-detect hidden invalidating change
false behavioral invalidation rate
evidence reuse ratio
recertification amplification
interaction miss rate
successor-certification latency
successor-certification total cost
restricted/suspended certificate time
assurance debt by harm tier
```

The aim is not to maximize evidence reuse. It is to minimize lifecycle assurance cost **subject to the stale-authority bound**.

### Acceptance tests

Add the following to the runtime qualification corpus:

| Test | Injection | Expected result |
|---|---|---|
| Exact-context mismatch | Change any CCH dependency; present predecessor cert | Predecessor cannot authorize |
| Harmless changed dependency | Change a dependency outside claim closure | New cert required, but unrelated evidence is reusable |
| Reference drift | Change judge/protocol while production artifact is unchanged | Affected evidence becomes unsupported |
| Silent provider substitution | Same public alias, changed response distribution | Continual monitor or TTL backstop restricts affected cert |
| Interaction trap | Two modifications pass separately but fail jointly | Interaction closure forces joint recert |
| Cumulative envelope escape | Apply individually allowed changes until combined state leaves declared region | Fast path stops; recert/escalation required |
| Correlated evidence | Present several verifier records sharing one root benchmark | No false independence upgrade |
| Authority degradation | Remove one high-authority prerequisite claim | Only dependent authority disappears; no authority expansion |
| Monitor underpower | Drift detector lacks required sample power | Certificate cannot remain fully authoritative merely because no alarm fired |

### Relationship to RQ26

RQ18 and RQ26 protect different recursive failure surfaces.

RQ18 asks:

> Is a certificate still applicable after the system or environment changes?

RQ26 asks:

> Is the adaptive portfolio still improving against an external truth process rather than recursively agreeing with itself?

They meet at model/provider drift, reference-protocol changes, audit freshness, task-distribution drift, and promotion cadence.

A portfolio candidate can pass RQ26's external-grounding requirements but still invalidate an old certificate because its model, prompt, router, or verifier identity changed.

Conversely, a perfectly current certificate can still describe a recursively biased system if the evidence process itself has become epistemically circular.

The architecture therefore needs both:

$$
\boxed{
\text{certificate-context integrity}
}
$$

and

$$
\boxed{
\text{external epistemic grounding}.
}
$$


## Model Factory and governed learning loop

The Model Factory is where this architecture becomes economically transformative.

The core principle is:

> **Production is a continuously accumulating experiment, but authenticated observations become training data only through a separate evidence, labeling, curation and promotion pipeline.**

Authentication proves **who emitted a trace and which execution it came from**. It does not prove that the trace is factually correct.

A production trace envelope should contain at least:

| Field family | Required information |
|---|---|
| Identity | `run_id`, `step_id`, authenticated SPIFFE principal, role |
| Model | semantic endpoint, provider, model/version or digest, tokenizer/prompt-template version where relevant |
| Context | request/context-manifest digest, data classification, retrieval manifest |
| Artifact | input and output digests, candidate revision, dependency digests |
| Policy | effective-policy digest, capability profile, routing-policy version |
| Verification | gate/checklet IDs, observations, evidence IDs, oracle profile, independence profile |
| Epistemic lineage | producer/verifier/teacher lineage IDs, dataset-manifest refs, evidence-family IDs, root-evidence refs/classes, recursive generation depth |
| Routing support | logging-policy ID, selected model, propensity/support where defined, exploration/shadow class |
| Audit | audit-stream ID, uniform/targeted role, sampling probability where defined, training-exclusion flag |
| Effects | requested action, grant reference, effect-slot ID, operation state, provider receipt |
| Outcome | terminal state, verified/waived/human status, later incident or escaped defect |
| Economics | token use, wall latency, queue latency, GPU time, provider cost |
| Provenance | worker image digest, code version, runtime environment, schema versions |
| Data governance | privacy class, retention class, permissible training use, deletion lineage key |

Do **not** make hidden model chain-of-thought a required trace primitive. Observable prompts, outputs, structured plans where explicitly produced, tool requests, tests, evidence and terminal decisions are sufficient for route and outcome learning and substantially easier to govern.

The complete data flow should be:

```mermaid
flowchart LR
    PROD[Production runs]
    ING[Authenticated<br/>trace ingress]
    RAW[Raw immutable<br/>trace zone]
    PRIV[Privacy / licensing /<br/>retention filter]
    CUR[Dedup + quality<br/>curation]
    JOIN[Outcome + oracle +<br/>incident label join]
    QUAL[Label-qualified<br/>examples]
    MAN[Signed dataset<br/>manifest]
    RTR[Router trainer]
    DST[Specialist / distillation<br/>trainer]
    VTR[Verifier trainer]
    EV[Independent evaluation]
    CAND[Candidate registry]
    CERT[Core certification /<br/>promotion gate]
    ACTIVE[Active portfolio]

    GOLD[Frozen evaluation<br/>and audit vault]
    EXTAUD[Fresh uniform external audit<br/>excluded from training]
    EXTANCHOR[Independent external outcomes /<br/>human / executable oracles]

    PROD --> ING --> RAW --> PRIV --> CUR --> JOIN --> QUAL --> MAN
    EXTANCHOR --> JOIN
    MAN --> RTR
    MAN --> DST
    MAN --> VTR

    RTR --> EV
    DST --> EV
    VTR --> EV

    GOLD --> EV
    EXTAUD --> EV

    EV --> CAND --> CERT --> ACTIVE
    ACTIVE --> PROD

    GOLD -. "NEVER flows to training" .-> MAN
    EXTAUD -. "NEVER flows to training" .-> MAN
```

NeMo Curator is a strong fit for the curation stage. NVIDIA's current Curator includes heuristic/model filtering and exact, fuzzy and semantic deduplication pipelines and scales through Ray/RAPIDS. citeturn24search3turn24search11 The broader research literature supports treating dataset composition as a first-class optimization variable: DataComp-LM found substantial performance sensitivity to data curation strategy, SemDeDup showed the utility of semantic deduplication, and DoReMi demonstrated learned domain-mixture weighting. citeturn22academia0turn22academia3turn21academia0

The recommended dataset state machine is:

| State | Entry requirement | Permitted use |
|---|---|---|
| `raw_authenticated` | authenticated workload/event provenance | forensics only |
| `policy_eligible` | privacy, consent, licensing, retention checks | curation |
| `curated` | exact/near/semantic dedup and corruption filtering | candidate labeling |
| `evidence_joined` | oracle/effect/incident outcomes linked | label computation |
| `label_qualified` | minimum oracle/independence requirements met | eligible training |
| `split_locked` | train/calibration/test ownership frozen | experiment |
| `manifested` | content hashes and provenance signed | reproducible training |
| `used_in_candidate` | dataset manifest attached to checkpoint | lineage tracking |
| `revoked` | source/policy/incident invalidated lineage | excluded; descendants reviewed |

Keep **raw traces, training data, calibration data, certification holdouts and permanent production audits as separate data roles**. The Core already requires offline certification, confirmatory holdout and continuing audit not to be conflated. fileciteturn0file0

A crucial anti-leakage rule is:

> **Sibling traces from the same task, user session, repository issue or synthetic seed must not straddle training and certification sets.**

Chronological holdouts should also be retained to expose temporal drift.

**Label provenance should be explicit rather than collapsed into one `correct=true` field.**

The preferred hierarchy is:

```text
formal/executable oracle
        ↓
independent hard verifier
        ↓
claim/source verification
        ↓
expert human adjudication
        ↓
calibrated independent verifier model
        ↓
weak heuristic / self-judgment
```

But this is not a total epistemic ordering; the Core's `OracleProfile` and `IndependenceProfile` should travel with each label. fileciteturn0file0

A training record might therefore have:

```json
{
  "example_id": "ex_...",
  "input_digest": "sha256:...",
  "candidate_model": "cheap_executor:v17",
  "observed_success": true,
  "label_source": "integration_test",
  "oracle_class": "executable",
  "oracle_applicability": "exact",
  "principal_independent": true,
  "evidence_family": "ci-run-742",
  "cost_usd": 0.0037,
  "latency_ms": 1940,
  "routing_propensity": 0.12
}
```

The `routing_propensity` is important. Once a router chooses which models see which traffic, naive training on only observed outcomes creates selection bias. Maintain a small, policy-safe exploration stream in low-risk strata so competing models occasionally receive the same tasks and the factory can estimate counterfactual routing value. High-risk tasks should never be randomized into an otherwise prohibited model merely to obtain data.

### The router factory

Do not begin with a large neural router.

The recommended evolution is:

```text
hard policy and workflow-stage rules
        ↓
simple calibrated classifier
        ↓
per-model success predictors
        ↓
cost / latency / failure predictors
        ↓
selective route policy with abstention
        ↓
agent-trajectory / step-level router
```

RouteLLM demonstrated that routing learned from model preference/outcome data can recover much of the strong model's quality while using the strong model less often. citeturn20academia12 But LLMRouterBench's 2026 reevaluation is especially important for this system: across a broad common evaluation, many sophisticated routers clustered closely, some failed to beat simple baselines, and a significant portion of the oracle gap remained a model-recall problem; larger model ensembles also showed diminishing returns. citeturn19academia3

Therefore the portfolio should stay **small and deliberately diverse** rather than accumulating every model accessible through an API.

The model-specific predictor is:

$$
\hat p_m(x,s,e)=
P(\text{qualifying success}\mid
x,\text{workflow stage }s,\text{evidence }e,\text{model }m)
$$

where qualifying success is defined by the Core's reference protocol rather than a self-reported model score.

The router first computes the policy-eligible set:

$$
\mathcal E(x)=
\{m:\text{privacy, capability, residency, risk and availability constraints pass}\}
$$

and only then chooses among those models.

A policy might be:

$$
m^* =
\arg\min_{m\in\mathcal E}
E[C_m]
$$

subject to:

$$
LCB(\hat p_m)\ge q_{\min}
$$

and the Core's higher-tier risk and authority constraints.

TwinRouterBench is particularly relevant because it evaluates model routing at the **individual step level of agentic trajectories**, including live coding-agent settings, rather than reducing routing to isolated single-turn prompts. citeturn19academia0 That should be the evaluation style adopted here.

### The specialist and distillation factory

The system should look for **repeatable slices where frontier capability has become teachable and verifiable**.

A task slice becomes a distillation candidate when:

```text
volume is substantial
AND frontier model succeeds consistently
AND a qualifying oracle/verifier exists
AND task distribution is sufficiently stable
AND cheap student has plausible capacity
AND projected serving savings exceed training + validation cost
```

The distillation ladder should be:

```text
verified demonstrations
      ↓
supervised fine-tuning
      ↓
on-policy distillation
      ↓
multi-teacher / cross-tokenizer distillation where useful
      ↓
optional constrained RL
```

On-policy distillation is preferable to blindly cloning static teacher completions when the student's own generation distribution matters. Generalized Knowledge Distillation explicitly trains against teacher feedback on student-generated sequences to reduce the train/inference distribution mismatch. citeturn23academia2 NVIDIA's current NeMo RL implementation now exposes on-policy distillation and supports multi-node student/teacher configurations; its newer documentation also includes multi-teacher and cross-tokenizer distillation variants. citeturn24search0turn24search4turn24search17

An official NeMo RL-style experiment can start from the documented pattern:

```bash
uv run python examples/run_distillation.py \
  policy.model_name="Qwen/Qwen3-1.7B-Base" \
  teacher.model_name="Qwen/Qwen3-4B" \
  cluster.gpus_per_node=8
```

The concrete teacher and student should of course be replaced with the chosen portfolio; the point is that current NeMo RL has an operational distillation path rather than requiring a custom trainer from scratch. citeturn24search0

NeMo Data Designer can supplement genuine production examples with synthetic edge cases, and current NVIDIA documentation supports generating through NVIDIA, OpenAI-compatible and vLLM-backed endpoints. citeturn24search2turn24search13 Synthetic data should remain provenance-tagged and should never silently acquire the same evidence status as independently observed production outcomes.

For reasoning-heavy tasks, teacher rationales can be useful supervision, as work such as Distilling Step-by-Step demonstrated, but the Factory should distinguish “teacher-generated explanation” from independently verified reasoning evidence. citeturn23academia0

### The verifier factory

Verifier models require **stricter lineage than producers**, because systematic verifier errors can silently turn into false authority.

The lifecycle should be:

```text
failure corpus
  ├── deterministic failures
  ├── escaped production defects
  ├── adversarially generated failures
  ├── human-adjudicated near misses
  └── verified clean controls
          ↓
verifier training
          ↓
calibration
          ↓
independence analysis
          ↓
shadow
          ↓
advisory
          ↓
scoped gate authority
          ↓
continuous random audit
```

A verifier must never obtain production block/waiver authority merely because its validation accuracy is high. The Core requires its schema, evidence, oracle and calibration boundaries to be valid, and its authority remains slice-specific. fileciteturn0file0

Particularly dangerous factory loops are:

```text
verifier V labels data
    ↓
train V2 on V's labels
    ↓
evaluate V2 on more labels from V
```

and:

```text
teacher produces answer
    ↓
teacher says answer is correct
    ↓
student trains on "verified" teacher answer
```

Both create provenance-family collapse.

Every verifier-training label should therefore record the evidence family that produced it. A second model family can improve model independence but does not create independent evidence when both models depend on the same incorrect source or test harness.



### Closed-loop epistemic stability and feedback monoculture

The Model Factory is a recursive adaptive system, not a one-way MLOps pipeline. Its deployment decisions alter which examples are observed, which models generate them, which verifiers label them, which examples qualify for training, and which distributions future models encounter.

The resulting research problem is:

> Under repeated **trace → selection → training → evaluation → deployment** cycles, when does the portfolio move toward lower *externally grounded* error rather than toward internally self-consistent correlated mistakes, evaluator preferences, or deployment-induced distribution artifacts?

There is no defensible universal answer such as “keep 10% human data.” The relevant quantity is **effective independent correction relative to the loop's endogenous error-amplification gain**.

#### State-space model

Let

$$
X_t=
\left(
P_t,\Theta_t,\Phi_t,\Pi_t,\mathcal D_t,G_t
\right),
$$

where $P_t$ is the external task/environment distribution, $\Theta_t$ the producer/specialist portfolio, $\Phi_t$ the verifier/evaluator portfolio, $\Pi_t$ the routing policy, $\mathcal D_t$ the learning/evaluation data state, and $G_t$ the causal provenance graph.

Let

$$
U_t=
(
E_t,
A_t,
\Xi_t,
\Gamma_t
)
$$

represent controllable exogenous evidence, audit allocation, policy-safe exploration, and promotion/adaptation cadence. With stochastic disturbance $\xi_t$,

$$
\boxed{
X_{t+1}=F(X_t,U_t,\xi_t).
}
$$

The scalar recursion sometimes used for intuition,

$$
e_{t+1}\approx (1-\alpha_{\mathrm{eff}})g\,e_t+\eta_t,
$$

is only a one-dimensional linearization of this richer system. In that approximation, stability requires

$$
(1-\alpha_{\mathrm{eff}})g<1,
$$

but neither $g$ nor $\alpha_{\mathrm{eff}}$ is universal or directly equal to a raw synthetic/real-data ratio.

#### Local stability and small-gain decomposition

Around an operating point $X^\star$,

$$
\delta X_{t+1}
=
A^\star\delta X_t+
B^\star\delta U_t+
W_t,
\qquad
A^\star=D_XF(X^\star,U^\star).
$$

A standard local condition is

$$
\boxed{\rho(A^\star)<1}.
$$

Because the learning loop is compositional, one can conceptually write

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

The empirical value of this decomposition is attribution: an injected blind spot can be followed through generation, selection, training, verification, and routing to identify which stage amplifies it.

#### Dynamical stability is not epistemic correctness

A loop may satisfy

$$
\rho(D_XF(X^\star))<1
$$

and still converge to a wrong fixed point.

Define externally grounded risk

$$
R_{\mathrm{ext}}(X)
=
\mathbb E_{(x,y)\sim P_{\mathrm{external}}}
[\ell(X;x,y)].
$$

A successful self-improving system therefore needs both

$$
\rho(D_XF(X^\star))<1
$$

and

$$
R_{\mathrm{ext}}(X^\star)-R^\star\le\epsilon
$$

for the declared reference process and protected task slices.

Internal verifier agreement, lower training loss, greater router confidence, or increased specialist traffic share cannot establish the second condition.

#### Effective independent information

Raw external-data percentage is a poor proxy for epistemic correction because nominally distinct labels may share the same causal blind spot.

Let $Y$ denote external truth, $H_t$ everything already encoded in the recursive portfolio history, and $E_t$ newly acquired external evidence. A conceptual quantity for fresh grounding is

$$
\boxed{
\mathcal I_t^{\mathrm{ext}}
=
I(Y;E_t\mid H_t).
}
$$

This measures how much information about the external reference arrives that was not already present in the recursive system. It is a theoretical definition, not a required production estimator.

If all later evidence is merely a stochastic transformation of current internal information,

$$
Y\rightarrow H_t\rightarrow H_{t+1},
$$

then the data-processing inequality gives

$$
I(Y;H_{t+1})\le I(Y;H_t).
$$

Recursive computation can reorganize existing evidence. Under this model it cannot create new information about an unobserved external truth. This is why the external evidence channel must remain live even when the internal portfolio becomes highly capable.

#### Provenance as a recursive graph

The model/dataset/evidence lineage graph can be normalized for analysis into an absorbing Markov chain

$$
P=
\begin{pmatrix}
Q&R\\
0&I
\end{pmatrix},
$$

where $Q$ contains internal-to-internal ancestry and $R$ transitions to independent external evidence roots.

The fundamental matrix

$$
N=(I-Q)^{-1}
$$

gives expected internal ancestry visitation before absorption, and

$$
B=NR
$$

gives absorption probabilities into the external evidence families.

Candidate diagnostics are:

$$
\tau=N\mathbf 1
$$

for expected recursive ancestry depth and

$$
\rho(Q)
$$

for recursive persistence. As $\rho(Q)\rightarrow1$, epistemic lineage can circulate internally for increasingly long periods. A closed internal communicating class with $\rho(Q)=1$ represents an epistemically self-referential region of the provenance graph.

For absorption probabilities $B_{ij}$, define

$$
H_i=-\sum_j B_{ij}\log B_{ij},
\qquad
N_{\mathrm{root},i}^{\mathrm{eff}}=e^{H_i}.
$$

This distinguishes nominal source count from effective root diversity.

#### Common-mode evaluator error

Evaluate the producer/verifier portfolio on a common independently grounded audit set. Let

$$
r(x)=
(r_1(x),\ldots,r_K(x))^\top
$$

be residual errors and

$$
\Sigma=\operatorname{Cov}(r)
$$

their covariance matrix.

If

$$
\lambda_1\ge\cdots\ge\lambda_K
$$

are eigenvalues, define common-mode concentration

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

define effective rank

$$
\boxed{
r_{\mathrm{eff}}
=
\exp\left(-\sum_i p_i\log p_i\right).
}
$$

A system with twenty nominal verifiers can still have $r_{\mathrm{eff}}\approx2$ if their errors span only two effective failure directions. Rising $C_{\mathrm{common}}$ or falling $r_{\mathrm{eff}}$ can therefore be an early monoculture signal even while raw agreement increases.

#### Routing creates selective observation

If a logging router selects model $m$ on task $x$ with probability

$$
\pi_0(m\mid x),
$$

counterfactual evaluation of target policy $\pi_1$ requires overlap wherever the target policy places mass.

Importance weights are

$$
w_i=
\frac{\pi_1(m_i\mid x_i)}
     {\pi_0(m_i\mid x_i)},
$$

with effective sample size

$$
\boxed{
n_{\mathrm{eff}}
=
\frac{(\sum_iw_i)^2}{\sum_iw_i^2}.
}
$$

A router can look increasingly successful while $n_{\mathrm{eff}}$ for alternatives collapses. At that point the system has not shown those alternatives are inferior; it has removed the observational support needed to compare them.

For domains where deployment changes future outcomes, the relevant quantity is interventional:

$$
R(\theta,\pi)
=
\mathbb E[
\ell
\mid
\operatorname{do}(\Pi=\pi)
].
$$

This is the performative component of RQ26.

#### Distribution and tail stability

Let

$$
P_t^{\mathrm{incoming}}
$$

be the incoming task distribution and

$$
P_t^{\mathrm{training}}
$$

the selected learning distribution. A candidate selection-distortion measure is

$$
\boxed{
D_{\mathrm{selection},t}
=
W_p(
P_t^{\mathrm{incoming}},
P_t^{\mathrm{training}}
).
}
$$

The exact distance need not be Wasserstein in production; the experiment should retain it only if it predicts failure better than simpler stratified drift measures.

Mean error is likewise insufficient. For protected stratum $S_j$,

$$
R_j(t)=
\mathbb E[
\ell_t\mid X\in S_j
].
$$

The program should separately track protected-stratum risk, acceptance/completion coverage, chronological holdouts, and when useful a tail functional such as

$$
\operatorname{CVaR}_\alpha(L_t).
$$

A head improvement that destroys rare but consequential modes is not genuine portfolio improvement.

#### Epistemic decoupling

The characteristic pre-failure signature is:

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

moves adversely.

Call this **epistemic decoupling**.

Agreement itself is therefore not a monotone safety metric. Rising agreement combined with rising residual-error correlation and falling root diversity is evidence for monoculture, not against it.

#### Audit must outrun adaptation

Suppose a protected slice has maximum tolerable external error $\epsilon$. With zero observed failures among $n$ effectively independent uniform audit items, the one-sided exact upper bound at confidence $1-\delta$ is

$$
p_{\mathrm{upper}}
=
1-\delta^{1/n}.
$$

To establish

$$
p_{\mathrm{upper}}\le\epsilon
$$

requires

$$
n
\ge
\frac{\ln\delta}{\ln(1-\epsilon)}
\approx
\frac{-\ln\delta}{\epsilon}.
$$

At 95% confidence this is the familiar rule-of-three scale, approximately $3/\epsilon$.

The architectural implication is not “always collect N examples.” It is:

> **Do not let consequential adaptive promotions outrun the independently powered audit window needed to support the affected risk claim.**

For continuously monitored audits, anytime-valid confidence sequences or e-processes are natural research candidates because they remain valid under continuous observation and data-dependent stopping, provided the audit sampling assumptions hold.

#### Epistemic viability as a control problem

The eventual target is a viable operating region

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

The control inputs are audit allocation, external-label acquisition, route exploration, training mixture, and promotion cadence. The long-run engineering objective becomes

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

In words:

> **Minimize the cost of independent external grounding subject to keeping the adaptive portfolio epistemically viable.**

The exact boundary of $\mathcal K$ is an empirical research result, not a constant to hard-code into the Core.

#### Operational consequences for the Factory

Until that boundary is known, the Factory should enforce the following posture:

- retain explicit root-evidence, model, verifier, teacher, and dataset lineage;
- preserve original independently grounded data rather than recursively replacing it by default;
- separate uniform external audit from targeted learning;
- prevent frozen certification and confirmatory holdouts from flowing into training;
- record routing support/propensity wherever counterfactual route claims are intended;
- maintain policy-safe exploration or paired shadow evidence in low-risk slices where alternatives would otherwise become unobservable;
- compare internal calibration with calibration on fresh externally grounded audits;
- analyze residual-error dependence, not merely verifier agreement;
- monitor protected tails and chronological holdouts;
- reject any candidate whose principal correctness case is produced solely by descendants of the same recursive evidence family;
- slow, bound, or stop adaptation when the external audit cannot keep pace.

The research program should vary external-evidence rate, evidence-family correlation, producer/verifier lineage overlap, exploration, specialist concentration, synthetic accumulation versus replacement, task drift, oracle strength, tail prevalence, and promotion cadence. The output should be a **stability map**, not a universal percentage:

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

### The promotion boundary

The Factory may automate everything through candidate creation:

```text
data discovery
curation
label joining
dataset generation
training
benchmark execution
calibration
comparison
shadow deployment
candidate report
```

The last transition must be:

```text
candidate
   ↓
Core promotion monitor
   ↓
certified / human-approved / rejected
```

A new router or model can be promoted only if the Core's lexicographic hierarchy passes:

1. structural invariants remain intact;
2. authority constraints remain valid;
3. severe-risk bounds remain satisfied;
4. selective-risk guarantees and coverage floors remain satisfied;
5. final quality is noninferior;
6. only then are cost and latency improvements considered.

This is also the right response to safe-RL research. Safe RLHF explicitly separates a safety cost from a helpfulness reward rather than assuming a single scalar reward can safely price all outcomes, while later high-confidence safe-RL work likewise emphasizes constrained safety evaluation. citeturn26academia1turn26academia3 The Core's lexicographic policy is stricter still and should remain authoritative.

## Component decision matrix and failure analysis

The following is the concrete 2026 stack I would choose.

| Component / function | NVIDIA option | Kubernetes / cloud option | Strong open-source option | Recommended choice | TCB? | Rationale | Important failure mode |
|---|---|---|---|---|---|---|---|
| Workload identity | OpenShell/NVIDIA service identities at product boundaries | EKS Pod Identity, GKE WIF, AKS Workload Identity | **SPIFFE/SPIRE** | **SPIFFE/SPIRE internally + native cloud identity at cloud edge** | **Yes** | Portable cryptographic workload identity; CSP federation only where required. citeturn13search7turn14search1turn14search0turn15search8 | Root/attestor compromise |
| Policy composition | OpenShell uses OPA for network policy | cloud IAM / admission / gateway policy | **OPA**, Cedar | **Typed Core composer + signed OPA bundles** | **Yes** | OPA is mature enforcement; Core merge algebra remains explicit. citeturn15search0turn15search6 | Stale or miscomposed policy |
| Pack/spine composition assurance | none | custom registry / policy controller | custom linter + proof checker | **Signed composition manifests + typed interaction hypergraph + `COMP-L0…L3` certificates** | **Assurance TCB where it gates activation** | Prevents independent certificates from being treated as automatically compositional; scopes additional assurance to unresolved interactions. | Missed hidden interaction or overbroad recertification |
| Secrets | NVIDIA product-specific secret integrations | AWS/GCP/Azure secret/KMS services | **Vault** | **Cloud KMS/HSM in managed production; Vault where portability matters** | **Yes** | Keep credentials and signing keys outside agents. citeturn13search1turn13search5 | Secret exfiltration/key compromise |
| Authorization monitors | None maps exactly | custom services | custom service | **Small custom Go/Rust services** | **Yes** | Core-specific semantics should not be delegated to an agent framework. | Authority amplification |
| Runtime Tool Broker | OpenShell gateway partially overlaps | API gateway/service mesh insufficient alone | custom broker | **Custom broker** | **Yes** | Must understand ActionContract, ResourceHandle, AuthorityGrant and EffectSlot. | Bypass path |
| Effect-slot state | None | managed SQL | **PostgreSQL** | **PostgreSQL SERIALIZABLE + unique constraints** | **Yes** | Strong transactional state for semantic cardinality. citeturn11search0 | Double commit / split writer |
| Workflow durability | NeMo Agent Toolkit is orchestration/eval, not durable-effect authority | AWS Step Functions and equivalents | **Temporal** | **Temporal** | **No security; yes liveness** | Excellent crash recovery while broker preserves authority semantics. citeturn12search6turn12search12 | Activity replay/retry |
| Invalidation propagation | no exact Core equivalent | Kafka/PubSub/Event Hubs | **NATS JetStream / Kafka** | **Dedicated replicated JetStream stream; Kafka if incumbent** | **Yes for freshness** | Monotonic durable watermark is security-relevant. citeturn16search1turn16search14 | Lag/partition/stale monitor |
| Distributed infrastructure lease | K8s-native | Kubernetes Lease | K8s Lease | **K8s Lease for leader election only** | No | Good lightweight coordination, but not semantic effect cardinality. citeturn10search3 | Mistaking lease for effect transaction |
| Semantic integration lease | none | SQL/strong DB | PostgreSQL | **Epoch/lease row in authority DB** | **Yes when authority-relevant** | Same consistency domain as effect state. | Dual integration authority |
| Arbitrary CPU sandbox | **OpenShell** | RuntimeClass / VM isolation | **Kata, gVisor, Firecracker** | **Kata/microVM for high risk; gVisor/OpenShell for development** | **Yes** | Defense against hostile generated code. citeturn3search0turn3search1turn3search5turn9search7 | Kernel/runtime escape |
| GPU isolation | GPU Operator, MIG, vGPU | dedicated cloud GPU VMs | VM + passthrough | **Dedicated GPU VM/node for hostile work; MIG for controlled same-host separation** | **Yes when containment depends on it** | Time-slicing lacks MIG's memory/fault isolation. citeturn28search4turn28search5 | Cross-workload fault/leakage |
| GPU scheduling | GPU Operator/DRA | Kubernetes DRA | device plugins/schedulers | **GPU Operator; established production allocation; evaluate DRA separately** | No | NIM's current DRA integration remains Tech Preview. citeturn28search0turn28search1 | Scheduler outage/resource fragmentation |
| NVIDIA model packaging | **NIM** | KServe | vLLM/SGLang | **NIM where NVIDIA optimization wins benchmark** | No | Excellent optimized serving product, but model execution is untrusted. | Bad model/output |
| Portable LLM serving | NIM/Dynamo | **KServe** | vLLM/SGLang | **KServe/vLLM as portable second path** | No | Avoid vendor lock-in; advanced KServe LLM path is mature. citeturn28search2turn28search15 | Serving mismatch/version drift |
| Semantic model routing | **Switchyard** | gateway-specific routers | custom/RouteLLM-style | **Own ModelRouter API with Switchyard adapter** | No | Current Switchyard aligns closely with strong/weak model routing. citeturn28search16 | Misroute to inadequate model |
| Replica/KV routing | **Dynamo** | KServe/llm-d | vLLM stack | **Dynamo for NVIDIA-dense deployment; KServe otherwise** | No | Serving optimization should remain below semantic routing. | Cache/load imbalance |
| Artifacts | NIMCache is model caching, not general authority store | S3/GCS/Blob | **Ceph RGW via Rook** | **S3 cloud / Ceph private, content-addressed** | No integrity; availability dependency | Digest verification removes storage from integrity TCB. citeturn18search8turn18search0 | Loss/unavailability/corruption |
| Authority ledger | no exact equivalent | relational DB + WORM | PostgreSQL + cryptographic attestations | **Postgres signed append log + WORM witness** | **Yes** | Separates transactional authority from independent tamper evidence. | Ledger rewriting |
| Provenance signing | NVIDIA manifests can participate | cloud KMS / artifact signing | **Sigstore/in-toto** | **OCI artifacts + signed attestations + KMS/HSM** | **Promotion verifier/key path: Yes** | Reproducible model/dataset/software identity. citeturn6search2turn6search12 | Unsigned/substituted artifact |
| Operational observability | NeMo Agent Toolkit / NeMo observability | provider logging | **OpenTelemetry** | **OTel + Prometheus/ClickHouse/Grafana** | No | Diagnostics should not create authority. citeturn7search1turn7search9 | Trace loss/spoofing |
| Evidence trace ingest | NVIDIA observability can supply input | custom secure ingest | custom | **Separate authenticated evidence-ingest service** | **Yes where evidence is authority-relevant** | A generic trace collector is not a proof system. | Fabricated evidence |
| Data curation | **NeMo Curator** | cloud ETL | Ray/Spark/custom | **NeMo Curator + Core provenance layer** | No | Strong accelerated filtering/dedup pipeline. citeturn24search3turn24search11 | Poisoning/leakage |
| Synthetic data | **NeMo Data Designer** | managed GenAI pipelines | custom | **Optional Data Designer** | No | Useful for edge cases, but synthetic provenance must remain distinct. citeturn24search2turn24search13 | Synthetic-error amplification |
| Distillation / RL | **NeMo RL / Gym / ModelOpt** | managed training services | general PyTorch stack | **NeMo RL for NVIDIA training; portable dataset/model contracts** | No | Current stack directly supports on-policy and multi-teacher distillation. citeturn24search0turn24search4 | Teacher-error inheritance |
| Router training | Switchyard ecosystem | custom ML service | RouteLLM-style classifier | **Custom calibrated success predictors** | No | Business/task distribution is specific to this system. citeturn20academia12turn19academia3 | Selection bias / poor frontier recall |
| Verifier training | NeMo training stack | custom ML | PyTorch/NeMo | **Custom lifecycle on NeMo/PyTorch** | No | Verifier is epistemic, not effect authority. | Correlated verifier failure |
| Certification durability | none | database/event/monitor primitives | custom | **CCH resolver + `CertificationClosurePlus` + successor-certificate service** | **Yes where it gates authority** | Exact-context invalidation with scoped evidence carry-forward; hidden-drift monitor + residual TTL | Stale certificate or over-invalidation |
| Certification | NVIDIA eval tools are useful inputs | cloud eval products | custom | **Reusable Core Certification Governor** | **Yes** | No vendor evaluator implements the Core's closure-bound authority semantics. | Self-certification |

The resulting design uses NVIDIA aggressively where NVIDIA's strengths actually matter—GPU lifecycle, optimized inference, model routing experiments, data curation and post-training—without making NVIDIA components the constitutional authority of the system.

The major failure modes are correspondingly easier to reason about:

| Failure | What happens without protection | Required mitigation |
|---|---|---|
| Router compromised | All traffic routed to weak or attacker-selected model | Router cannot issue grants; hard eligibility filter; verification and certification independent |
| Producer prompt-injected | Requests malicious external action | Semantic action contract + broker authorization + no credentials + resource-bound grant |
| Grant copied to another workload | Unauthorized use | mTLS/SPIFFE principal binding |
| Monitor signing key stolen | Fake grants/certificates | per-monitor keys, HSM/KMS custody, short validity, revocation event, no universal signer |
| Policy bundle stale | Old permission used after tightening | policy digest in grant; signed bundle; precommit policy/watermark recheck |
| Pack assumption escape | individually valid pack runs outside its certified environment after composition | predecessor-set contract discharge + usage-domain check before activation |
| Shared-state interaction | local invariant is invalidated by another pack's writes | read/write interaction graph + frame/ownership/serialization/invariant-stability proof |
| Authority amplification across packs | combined capabilities create a higher-tier path neither pack had alone | restricted exact or conservative authority closure; provenance-bound per-call authorization |
| Correlated certificate evidence | same verifier/corpus/simulator/model family is counted as independent corroboration | evidence-provenance graph; dependence-aware confidence treatment |
| Unsupported hyperproperty composition | local guarantees are mistaken for end-to-end noninterference/confidentiality | named composition theorem + side-condition proof or `COMP-L2/L3` escalation |
| Invalidation bus delayed | revoked authority still appears active | fail closed when watermark freshness is unprovable |
| Broker crashes before provider call | workflow retries | operation remains reserved; retry joins same operation |
| Provider commits then connection dies | naive retry duplicates effect | mark `outcome_unknown`; query receipt/target state; never blind-retry |
| Provider has no idempotency/status API | effect outcome unprovable | independent state observation or human reconciliation; terminal unresolved state |
| Two regions think they own effect | duplicate authoritative transition | home-authority epoch; no concurrent writer; explicit epoch transfer |
| Temporal replays Activity | duplicate API invocation | broker effect slot makes replay harmless/joins prior state |
| Sandbox escapes network restrictions | credential theft / uncontrolled egress | no credentials in sandbox; host/network isolation; broker/proxy-only egress |
| Sandbox kernel escape | host compromise | Kata/microVM/dedicated nodes; patching; no authority service colocated |
| GPU time-slicing across adversarial tenants | weak isolation | full GPU/MIG/vGPU/dedicated VM rather than plain time-slicing |
| Verifier systematically wrong | bad artifact falsely accepted | objective gates first, independence/evidence profile, calibration, random audits |
| Telemetry collector compromised | fabricated “successful” trace | operational telemetry never qualifies as authority evidence |
| Training corpus poisoned | future router/model learns attack | signed lineage, quarantine, trust classes, dedup, holdout, source-level revocation |
| Router feedback loop | model never explores alternatives and learns from own selection | record routing propensity; controlled safe exploration; counterfactual replay |
| Epistemic decoupling | internal pass rate/agreement improves while fresh external risk worsens | uniform external audit, external calibration, root-lineage and tail diagnostics, slow/demote before ordinary quality threshold failure |
| Evidence-root collapse | many nominal labels/verifiers ultimately terminate in one causal evidence family | root-evidence lineage, effective root diversity, no automatic upgrade of recursive corroboration |
| Common-mode evaluator failure | distinct verifier instances share the same residual blind spot | common external audit matrix, residual covariance/effective-rank monitoring, non-model oracle where available |
| Audit/adaptation race | several recursive promotions occur before external audit can detect inherited error | gate consequential adaptation on independently powered audit windows; slow promotion or increase external sampling |
| Teacher labels own output | self-confirming distillation | independent oracle/verification required for high-authority data |
| Frozen eval leaks into training | apparent improvement with no generalization | physically separate evaluation vault and access policy |
| Provider silently changes model alias | certification assumptions become stale | endpoint fingerprint/probe set; version capture; invalidate affected closure |
| Certificate survives changed exact context | stale authority remains active after model/prompt/tool/schema/policy/reference mutation | exact CCH match at authorization; predecessor superseded; successor certificate required |
| Differential recertification misses interaction | component-local tests pass an unsafe combined change | `CertificationClosurePlus`; declared interaction edges; full recert when interaction support is unresolved |
| Recertification fatigue | teams bypass or weaken gates because every mutation reruns the world | explicit evidence applicability; scoped delta recertification; assurance-cost telemetry |
| Artifact store corrupted | malicious or accidental substitution | content digest checked on every authoritative read |
| Authority DB rewritten | false historical authority | signed per-monitor chains + independent WORM witnesses |
| TCB deployment supply chain compromised | attacker replaces broker/monitor | signed artifacts/provenance, protected deployment authority, staged rollout |
| Distribution drift | router and verifier calibration deteriorate | drift monitor, coverage reduction, auto-demotion to hard verification |

There is one particularly useful adversarial test for the architecture:

> Give the router, producer model and verifier model all the wrong answer simultaneously and ask whether an external authoritative effect can still occur without a valid grant.

If the answer is yes, the TCB is not actually minimal or the mediation boundary is incomplete.

A second adversarial test covers the independent RQ26 failure mode:

> Give the producer, router, specialist, and verifier a shared but controlled blind spot; let recursive training increase internal agreement and specialist traffic; then introduce fresh independently grounded cases that expose the blind spot. Does the system preserve the distinction between descendant agreement and external evidence, recover the causal lineage, block self-promotion, and reduce exposure or demote before external risk exceeds the declared bound?

The first test asks whether compromised intelligence can compromise authority. The second asks whether recursive intelligence can become its own source of truth without detection. Both must be addressed; passing one does not imply the other.

## Deployment progression and end-to-end validation

The deployment path should add scale without changing Core semantics.

| Stage | Runtime | Models | Security/control | Data/factory | Goal |
|---|---|---|---|---|---|
| **Laptop** | Docker/Kind/K3d, Temporal dev, PostgreSQL, single-node JetStream | frontier API + small local model | SPIRE test trust domain, OPA, Vault dev, custom broker, gVisor/OpenShell | local content-addressed artifacts, OTel | Prove invariants |
| **Single-node GPU** | k3s/Kubernetes + NVIDIA GPU Operator | one NIM or vLLM/Nemotron endpoint + frontier APIs | same broker/identity/policy; gVisor/Kata CPU sandbox | initial Curator + trace warehouse | Prove routing and model economics |
| **Private cluster** | Kubernetes, HA Postgres/Temporal/JetStream, Rook-Ceph | NIM/Dynamo and/or KServe/vLLM | SPIRE HA, KMS/Vault, Kata, MIG/dedicated nodes, signed ledger checkpoints | NeMo Curator/Data Designer/RL training | Production-scale reliability |
| **Hybrid multi-cloud** | per-region clusters; explicit authority home | regional local models + multiple managed frontier providers | SPIFFE federation, CSP workload identities, regional brokers, authority epochs | federated trace ingestion with governance boundaries | Resilience and portfolio optimization |

**Laptop.** The laptop target is not throughput. It is a complete proof that the control-plane invariants survive hostile executors.

A minimal repository can look like:

```text
core/
  policy-composer/
  authorization-monitor/
  runtime-broker/
  reconciler/
  evidence-ingest/
  authority-ledger/

workflow/
  temporal-worker/

router/
  model-router/
  switchyard-adapter/

sandbox/
  runner/

factory/
  trace-curator/
  label-join/
  router-trainer/
  evaluator/

schemas/
  action_contract.json
  authority_grant.json
  evidence.json
  artifact_manifest.json
  dataset_manifest.json
```

Switchyard can be stood up independently behind the interface using its current Python package/server pattern; NVIDIA's current routing system is intended to present virtual models over heterogeneous backends. citeturn28search16

At this stage, content-addressed artifacts can simply be:

```text
./artifacts/sha256/ab/cd/<full-digest>
```

The production abstraction should already expose `ArtifactStore`, so moving to S3/Ceph later does not affect callers.

**Single-node GPU.** Add one local Nemotron/NIM or vLLM-served model and compare it against one or two frontier providers. GPU Operator should manage the local accelerator. NIM can be introduced either directly or through its Kubernetes tooling. NVIDIA currently supports NIM deployment on Kubernetes and integrates NIM Operator with GPU resources, but its DRA-specific NIM integration should remain experimental until the Technology Preview designation is removed. citeturn28search0turn28search1

For a MIG-capable server, an installation follows the normal GPU Operator Helm pattern; the exact version must be pinned to the validated environment rather than tracking `latest`. At this stage, benchmark:

```text
NIM
vs.
vLLM
vs.
managed API

under:
1 / 4 / 16 / 64 concurrent calls
short / medium / long context
tool-calling / structured output / plain generation
```

Measure **cost per verified successful task**, not tokens per second in isolation.

**Private cluster.** Introduce high availability and strict tenant boundaries.

Recommended topology:

```text
control nodes:
    broker
    monitors
    policy
    identity
    reconciler
    authority DB clients
    no untrusted model workloads

inference nodes:
    NIM / Dynamo or KServe / vLLM
    GPU Operator
    no authority credentials

sandbox CPU nodes:
    Kata RuntimeClass
    network deny
    no GPU unless explicitly needed

GPU sandbox nodes:
    dedicated trust domain / VM
    preferably one hostile workload boundary per VM/node

training nodes:
    NeMo Curator / NeMo RL / Data Designer
    no production authority keys

data nodes:
    Postgres
    JetStream
    Ceph
    observability
```

NVIDIA's GPU time-slicing should be confined to workloads that may safely share a weaker isolation boundary; NVIDIA explicitly notes the absence of memory/fault isolation compared with MIG. citeturn28search4

**Hybrid multi-cloud.** Do not transform the authority plane into one giant stretched cluster.

Instead:

```text
                  GLOBAL CONTROL METADATA
                policy versions / trust roots
                    / model registry /
                   signed checkpoints
                         │
             ┌───────────┴───────────┐
             │                       │
       Authority Region A       Authority Region B
       epoch 451 active         standby / other runs
             │                       │
       local effect DB          local effect DB
       local broker             local broker
       local invalidation       local invalidation
             │                       │
      models/tools in A        models/tools in B
```

A run with active authority has one writer epoch. Model inference can be multi-region because it only produces candidates. Effect authority is more conservative.

Cloud-native workload identity should bridge only at the regional external-resource boundary: EKS Pod Identity, GKE Workload Identity Federation and AKS Workload Identity can supply short-lived cloud authorization without static credentials in workloads. citeturn13search7turn14search1turn14search0

The **minimal end-to-end demonstration** should validate these invariants in order:

| Test | Injection | Expected result |
|---|---|---|
| Identity non-forgeability | producer declares another principal in payload | authenticated SPIFFE identity wins; denied |
| No ambient authority | prompt asks model to directly send an email/push code | model has no credential/path |
| Grant scoping | valid grant used against different repository/resource | denied |
| Grant replay | same grant used twice | second authoritative use rejected/joined per operation state |
| Digest binding | mutate parameters after grant | digest mismatch; denied |
| Policy freshness | revoke resource after grant creation | precommit watermark/policy recheck aborts |
| Principal separation | producer submits own verification attestation | not qualifying evidence |
| Effect cardinality | kill broker after provider commit but before local completion | `outcome_unknown`; reconciled; no blind second effect |
| Workflow recovery | kill Temporal worker mid-run | workflow resumes without duplicating authority |
| Artifact integrity | corrupt stored artifact bytes | hash validation fails |
| Router compromise | force every prompt to cheapest model | quality may fall; authority/verification cannot be bypassed |
| Verifier compromise | verifier returns “clear” on known-bad artifact | deterministic/hard gate or audit catches; verifier cannot authorize |
| Sandbox containment | generated code attempts host/network/secret access | blocked by runtime/network boundary |
| Evidence spoofing | send forged OTel “all tests passed” span | diagnostic trace cannot become qualifying evidence |
| Training poisoning | introduce trace with invalid signature/provenance | excluded before training eligibility |
| Candidate self-promotion | training job attempts to mark model active | registry/promotion authority rejects |
| Epistemic closure | producer/router/specialist/verifier share a blind spot and recursive training raises internal agreement | fresh external contradiction remains distinguishable; causal lineage recovered; affected candidate cannot self-promote; exposure can be reduced/demoted |
| Counterfactual support collapse | routing concentrates until an alternative is rarely observed, then system claims the alternative is worse | comparison marked underpowered/unsupported unless overlap, logged propensity, or paired shadow evidence is sufficient |
| Audit/adaptation race | candidate generations are promoted faster than fresh external audit reaches preregistered power | further consequential promotion held or audit/external evidence increased |
| Composition contract escape | pack B requires an assumption that the configured predecessors do not jointly establish | activation blocked; unresolved dependency edge emitted |
| Shared-state interference | pack A mutates a cell used by pack B's certified invariant without a stability proof | `COMP-L0` rejected; interaction certificate required |
| Authority tier crossing | two individually bounded packs compose into a higher authority tier | activation blocked or escalated to required `COMP-L` scope |
| Evidence double-count | two certificates reuse the same verifier/corpus while aggregation assumes independence | confidence combination rejected until dependence is represented |
| Higher-order interaction | inject a defect that appears only for a three-pack + spine combination | hypergraph linter identifies the multi-component edge; pairwise-only credit rejected |
| Usage-domain escape | increase concurrency/tool count beyond one pack's certified envelope | modular credit invalidated; interaction/integration revalidation required |
| Certificate context mismatch | mutate model/prompt/tool/schema/policy/reference dependency and replay predecessor certificate | predecessor certificate is non-authorizing; successor required |
| Differential evidence reuse | mutate an unrelated dependency | predecessor superseded; unrelated evidence carried into successor without full rerun |
| Hidden model drift | keep model alias stable while behavior distribution changes | probe/anytime monitor or TTL backstop restricts affected certificate |
| Interaction closure | apply two independently passing changes that fail jointly | joint recertification required; no component-local successor certificate |
| Invalidation partition | monitor cannot establish fresh watermark | fail closed |
| Authority DB conflict | simulate dual operation attempts | serializable/unique effect-slot constraints prevent dual commit |

The defining acceptance test is:

```text
Compromise:
    producer
  + semantic router
  + cheap model
  + frontier model
  + verifier model
  + workflow worker
  + generic telemetry

Still must NOT permit:
    unauthorized authoritative effect
    unauthorized waiver
    protected-policy mutation
    false authority-ledger entry
```

If that test passes under realistic fault injection, the TCB boundary is doing real work.

## Evaluation framework and implementation roadmap

The Model Factory and routed runtime should be evaluated as one economic and reliability system, but **not with one scalar score**. That is exactly where the Core's sibling metrics and lexicographic promotion hierarchy become useful. fileciteturn0file0

The top-level quality equations remain:

$$
L_{\text{escape}}
=
\kappa R_{fw}+\nu R_v
$$

where the waiver path and qualifying verified path remain separately visible. Also preserve acceptance coverage $C_{accept}$ and completion coverage $C_{complete}$, so the system cannot improve its apparent safety simply by refusing everything. fileciteturn0file0

The runtime/factory dashboard should add the following:

| Surface | Primary metrics | Why |
|---|---|---|
| Accepted-artifact quality | `L_escape`, `R_accept`, `R_fw`, `R_v`, `κ`, `ν` | Core quality estimands |
| Coverage | `C_accept`, `C_complete`, human-deferral rate | Prevent fail-closed metric gaming |
| Routing quality | cheapest-sufficient-model accuracy, frontier-required recall, routing regret, OOD abstention | Measures harmful downgrades |
| Routing calibration | Brier score, reliability curves, slice calibration | Required for threshold policies |
| Portfolio economics | $/request, **$/verified-success**, frontier-call share, GPU-hours/success | Correct economic objective |
| Latency | p50/p95/p99 end-to-end, model call, verification and time-to-certification | User and assurance SLO |
| Verification | severe-defect recall, specificity, false-block rate, calibration, unique-catch rate | Verifier usefulness |
| Compositional assurance | contract-discharge completeness, unresolved interaction edges by type, `COMP-L` distribution, authority-tier crossings, evidence-dependence flags, usage-domain escapes, added certification scope/cost | Detect when modular assurance credit is no longer justified and measure whether scoping avoids unnecessary whole-system recertification |
| Authority safety | unauthorized-effect events, duplicate authoritative commits, grant violations | Structural security |
| Reconciliation | `outcome_unknown` frequency, unresolved fraction, time-to-reconcile | Real-world external-effect reliability |
| Invalidation | watermark lag, stale-decision attempts, fail-closed count | Freshness health |
| Certification durability | CCH mismatch/stale-cert attempts, invalidation precision/recall, evidence reuse, recert amplification, interaction misses, hidden-drift TTD, successor-cert cost/latency | Prevent stale authority without making every change globally expensive |
| Sandbox | blocked egress/host-access attempts, escape findings | Containment evidence |
| Data quality | lineage completeness, dedup rate, rejected provenance rate, split leakage | Factory input quality |
| Label quality | oracle distribution, independence strata, human agreement, later label reversals | Prevent noisy feedback loops |
| External grounding | fresh external risk, external-vs-internal calibration divergence, audit effective sample size, promotions per powered audit window | Detect self-consistency diverging from externally grounded performance |
| Epistemic lineage | externally rooted evidence fraction, recursive ancestry depth, effective root diversity, producer/verifier/teacher ancestry overlap | Detect causal monoculture before aggregate quality moves |
| Correlated error | residual-error correlation, unique-catch rate, dominant covariance-eigenmode share, covariance effective rank | Detect common-mode verifier/model failure |
| Counterfactual support | logging-policy overlap, route propensity support, off-policy effective sample size, paired shadow/random-route gap | Prevent router selection from making alternatives unobservable |
| Tail stability | protected-stratum risk and coverage, chronological-holdout gap, novelty/OOD risk, CVaR where appropriate | Prevent head improvements from hiding tail collapse |
| Factory productivity | candidates trained, shadow-pass rate, canary-pass rate, promotion rate | Engineering efficiency |
| Distillation | quality delta, cost reduction, latency reduction, frontier substitution rate | Whether capability actually moves downward |
| Drift | incoming-vs-training distribution shift, selection distortion, calibration drift, task-slice shift, provider/model-version changes | Recertification and epistemic-stability trigger |
| Model lineage | percentage of active checkpoints with complete signed provenance | Auditability |
| Compliance | data-retention violations, deletion-lineage completeness, policy exceptions | Governance health |

A useful router regret metric is:

$$
Regret_Q(x)=
Q(m_{\text{oracle}},x)-Q(m_{\text{route}},x)
$$

where the “oracle model” means the cheapest or best known model for that evaluation case based on exhaustive offline execution, not an omniscient metaphysical oracle.

More directly useful to this architecture is **false downgrade rate**:

$$
R_{\text{FD}}
=
P(\text{router selects inadequate cheaper model}
\mid
\text{a qualifying stronger model was required})
$$

and especially the severity-stratified upper bound on that quantity.

LLMRouterBench's broad 2026 evaluation is a strong warning not to optimize generic router accuracy alone: simple routing baselines remain competitive, and model recall and portfolio composition account for significant remaining opportunity. citeturn19academia3 TwinRouterBench further supports evaluating routing inside full agent trajectories, where the route at one step changes later state and therefore cannot always be assessed as an isolated classifier decision. citeturn19academia0

The benchmark progression should therefore be:

```text
Static model matrix
    every safe candidate model on every evaluation item
        ↓
Offline routing replay
        route over fixed model outcomes
        ↓
Trajectory simulation
        route over recorded agent states
        ↓
Shadow routing
        router chooses, incumbent still serves
        ↓
Paired canary
        new path on bounded live slice
        ↓
Governed production rollout
        permanent uniform audit
```

The Factory must use **two audit streams**:

```text
UNIFORM RANDOM AUDIT
    unbiased certification / drift estimation

TARGETED AUDIT
    oversample uncertainty, incidents,
    high-risk strata and new models
    for learning
```

Only analyses that account correctly for the sampling scheme should feed formal risk claims. The Core already makes that distinction between uniform certification sampling and targeted learning. fileciteturn0file0

Compliance should be treated as another source of policy constraints, not a late documentation exercise. NIST's Generative AI Profile extends the AI Risk Management Framework with GenAI-specific risk-management guidance, and NIST continues to emphasize test, evaluation, verification and validation in operational AI risk management. citeturn25search0turn25search2 In the EU, general-purpose AI obligations have been phased in since August 2025, with Commission enforcement milestones reaching August 2026, while transparency requirements under the AI Act also become applicable in August 2026 for covered systems. citeturn25search7turn25search18 The precise legal obligations depend on provider/deployer role and use case, but the architecture should already record the model, intended use, provenance, data categories, evaluations, human-oversight policy, incidents and downstream releases needed to support such governance.

The implementation order should deliberately put machine learning **after trustworthy observation**.

```mermaid
gantt
    title Recommended implementation sequence
    dateFormat YYYY-MM-DD

    section Trusted foundation
    Core schemas + invariant executable tests      :a1, 2026-08-17, 21d
    Pack composition manifest + linter            :a0, after a1, 21d
    SPIFFE identity + policy + key boundary        :a2, after a1, 21d
    Broker + grants + effect-slot transaction      :a3, after a2, 28d
    Invalidation + CCH/signed authority ledger     :a4, after a2, 28d
    Sandbox + egress isolation                     :a5, after a2, 28d

    section Durable execution
    Temporal workflow integration                  :b1, after a3, 21d
    Reconciliation + chaos tests                   :b2, after b1, 21d
    Content-addressed artifacts                    :b3, after a3, 14d

    section Heterogeneous inference
    Stable ModelRouter API                         :c1, after b1, 14d
    Switchyard + frontier + local model            :c2, after c1, 21d
    NIM/KServe GPU benchmark                       :c3, after c2, 28d

    section Model Factory
    Authenticated trace schema + data zones        :d1, after b2, 28d
    Curation + lineage + label joining             :d2, after d1, 28d
    Offline router baselines                       :d3, after d2, 21d
    Specialist distillation pilot                  :d4, after d2, 35d
    Verifier training/calibration                  :d5, after d2, 35d

    section Promotion
    Shadow router                                  :e1, after d3, 21d
    Candidate model shadow                         :e2, after d4, 21d
    Successor certification + canary               :e3, after e1, 28d
    Governed portfolio optimization                :e4, after e3, 35d
```

The milestones should be judged by **proofs**, not feature completion.

| Milestone | Exit criterion |
|---|---|
| **Trusted substrate** | No tested untrusted principal can create authoritative effect without broker/grant path |
| **Composition gate** | Seeded dependency/state/authority/evidence/usage-domain interactions cannot receive `COMP-L0`; unaffected packs retain modular credit |
| **Governed effect path** | Crash/timeout/replay experiments cannot exceed effect-slot cardinality |
| **Invalidation safety** | stale policy/grant/certificate is rejected before linearization |
| **Certificate durability** | any exact-context mutation makes the old certificate non-authorizing; unaffected evidence can be carried into a new CCH-bound successor only when applicability survives |
| **Sandbox boundary** | hostile test corpus cannot reach host credentials, unrestricted egress or authoritative write surfaces |
| **Heterogeneous serving** | at least one local/NVIDIA and one frontier provider interchangeable through semantic `ModelEndpoint` contract |
| **Authenticated learning corpus** | every eligible training example has trace, policy, model, artifact and label provenance |
| **Router baseline** | simple stage/policy router and best-single-model baselines established before learned router |
| **Router candidate** | improves Pareto frontier without violating severe-slice noninferiority |
| **Distilled specialist** | replaces expensive model on a bounded validated slice while preserving certified outcome bounds |
| **Verifier candidate** | calibrated and independently evaluated; no authority outside validated slices |
| **Factory automation** | traces can produce signed candidate datasets/checkpoints automatically |
| **Governed self-improvement** | automated Factory still cannot mark its own output production-active |

The highest-priority risks are not model-training risks. They are, in order:

**First: incomplete mediation.** One forgotten direct GitHub, database, shell, cloud, SMTP or deployment path can invalidate the entire authority model.

**Second: evidence laundering.** Ordinary logs, self-judgment or generated labels can accidentally become “verification” if evidence types are not encoded mechanically.

**Third: feedback contamination.** A router and verifier trained mostly on their own prior decisions can become confidently self-reinforcing.

**Fourth: multi-region authority ambiguity.** Availability engineering can accidentally weaken the single-authoritative-linearization requirement.

**Fifth: TCB accretion.** Every product added to the trusted path increases the number of components whose compromise can violate a Core invariant. Resist the temptation to put the agent framework, model gateway, workflow engine, model server or observability platform inside that boundary merely because doing so seems operationally convenient.

The architecture should ultimately produce this failure-containment property:

$$
\boxed{
\text{Compromised intelligence}
\not\Rightarrow
\text{compromised authority}
}
$$

while the Model Factory supplies a complementary economic property:

$$
\boxed{
\text{Repeated expensive verified behavior}
\Rightarrow
\text{candidate cheaper specialized behavior}
}
$$

but only after:

$$
\boxed{
\text{independent evaluation}
+
\text{risk certification}
+
\text{governed promotion}
}
$$

and with a separate epistemic-stability property:

$$
\boxed{
\text{recursive intelligence}
\not\Rightarrow
\text{recursive truth}
}
$$

implemented operationally by preserving fresh externally grounded evidence, causal evidence lineage, counterfactual observability, protected-tail audits, and an adaptation cadence that cannot outrun the audit process supporting the relevant risk claims.

That combination, together with interaction-scoped pack/spine assurance, exact-context certificate invalidation, and differential successor certification, is the deepest architectural consequence of joining the Reusable Core to a Nemotron-style routed model portfolio. The steady-state system is no longer best understood as “a group of AI agents.” It is a **governed adaptive computing platform**: probabilistic models supply abundant replaceable cognition; deterministic services provide checkable computation; a deliberately small TCB controls authority; and a separate Model Factory continuously compresses expensive capability into cheaper models without allowing the learning loop to become its own source of truth or permission.