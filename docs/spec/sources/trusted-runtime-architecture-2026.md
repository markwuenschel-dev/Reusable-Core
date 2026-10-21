> **Reusable Core v1.10 — Source: Trusted runtime architecture research**
>
> NON-normative source research (RUNTIME). Its adopted conclusions live in Volume II.
>
> **Precedence:** the [v1.10 kernel](../reusable-core-v1.10-kernel.md) wins any conflict with this document. Internal references to "v1.9" and to sibling documents by their former names are historical; see the [supersession map](../README.md#supersession-map).
>
> **Fidelity:** everything below the end-of-header marker is the source document reproduced byte-for-byte (`Trusted_Runtime_Architecture_for_the_Reusable_Core_in_2026.md`, SHA-256 `56ba27db1905d656`).

<!-- v1.10 volume header end -->
# Trusted Runtime Architecture for the Reusable Core in 2026

## Executive finding

The best concrete implementation of Reusable Core v1.9 is **not an “agent platform” and not an NVIDIA stack wrapped around an orchestrator**. It is a small, deliberately trusted authority plane surrounded by largely untrusted execution infrastructure.

The Reusable Core already specifies the essential semantic boundary: models and agents are replaceable executors; competence is distinct from authority; production is distinct from verification; routing cannot mint permission; consequential transitions require exact-object authorization; external effects pass through a broker; credentials are attached out of band; ambiguous effects are reconciled rather than blindly retried; and invalidation freshness is checked at authorization time. fileciteturn0file2

My recommended 2026 production architecture is:

| Concern | Recommended default |
|---|---|
| Production substrate | **Kubernetes** |
| Workload identity | **SPIFFE/SPIRE**, federated into AWS/GCP/Azure workload identity |
| Semantic effect authorization | **Cedar**, wrapped by a Core-owned authorization service |
| Cluster/platform policy | **OPA** as a secondary platform/admission layer |
| Secrets | **Vault or cloud secret manager**, reachable only by trusted brokers/controllers |
| Durable orchestration | **Temporal** |
| Authoritative transactional state | **PostgreSQL** |
| Invalidation/event distribution | **NATS JetStream**, with authoritative sequence state in PostgreSQL |
| Artifact/evidence storage | **Content-addressed S3-compatible object storage**, WORM for authority evidence |
| Ledger tamper evidence | Signed append-only PostgreSQL ledger **plus independent transparency/WORM checkpoints** |
| Ledger witness | **Private Rekor / independent Sigstore-style witness** or independently controlled WORM store |
| Arbitrary-code isolation | **Kata Containers** for hostile workloads; gVisor for lower-risk/high-density cells |
| Dedicated microVM option | **Firecracker** where you build a separate sandbox service |
| External-effect execution | Core-owned **typed Tool Broker + trusted adapters** |
| Coordination/leases | DB-backed lease + **fencing token**; etcd only when needed for distributed coordination |
| Observability | **OpenTelemetry + Prometheus-compatible metrics + GPU/DCGM telemetry** |
| NVIDIA GPU lifecycle | **NVIDIA GPU Operator** |
| NVIDIA model lifecycle | **NIM Operator** |
| NVIDIA-scale local inference | **NIM + Dynamo**, selectively |
| Vendor-neutral local inference | **KServe + vLLM/SGLang/TensorRT-LLM**, selectively |
| Provider/model abstraction | Core-owned stable inference contract in front of **Switchyard / LiteLLM / Envoy AI Gateway / cloud APIs** |
| Semantic model routing | Reusable Core router; learned router advisory until certified |
| Replica/KV routing | **Dynamo or Gateway API Inference Extension/KServe** |
| Multi-cloud design | **Federated execution planes around one authoritative home plane**, not active-active authority everywhere |

The key architectural decision is that **Temporal, NIM, Dynamo, Switchyard, NeMo Agent Toolkit, LLMs, model gateways, NATS, checklets, agent sandboxes, and most observability infrastructure do not need to possess effect authority**. A compromised component in that set should be able to waste compute, return malicious output, stall a workflow, or request an unauthorized operation—but should still be unable to create the authoritative external effect. That realizes the Core's security target:

```text
compromised reasoning  ⇏  unauthorized authoritative effect
```

fileciteturn0file2

That design choice drastically reduces the trusted computing base.

It also resolves the relationship to the earlier Nemotron research. Nemotron, NIM, Dynamo and Switchyard belong principally to the **heterogeneous intelligence/execution fabric**. The Reusable Core governs that fabric. Kubernetes, identity, storage, isolation, policy enforcement and the broker instantiate the infrastructure on which the Core's guarantees actually depend. Your earlier routing research correctly separated semantic model routing from lower-level inference routing; this architecture preserves that decomposition rather than allowing one “smart router” to become sovereign. fileciteturn0file1

My overall recommendation is therefore:

> **Build a trusted microkernel for authority, not a trusted monolith for agents.**

Everything that can safely be made advisory should be advisory. Everything that can safely be recomputed should be recomputable. Only identity, policy composition, exact-object authorization, effect-slot state, credential mediation, sandbox enforcement, authoritative state transitions, invalidation freshness and ledger integrity should sit on the shortest possible path to authority.

## Trust boundaries and reference architecture

The most important implementation exercise is deciding **what must be trusted to preserve the Core's invariants if everything else is malicious**.

SPIFFE is particularly well suited to this problem because its Workload API issues cryptographically verifiable workload identities independent of application-supplied identity claims. X.509-SVIDs can establish mutually authenticated channels, and SPIFFE explicitly supports foreign trust bundles for federation between trust domains. SPIFFE recommends X.509 identities where possible because bearer JWTs are more susceptible to replay. citeturn18search0turn18search1turn18search4

The resulting trust model should look like this:

```text
                            USER / CALLER
                                 │
                                 │ authenticated request
                                 ▼
┌──────────────────── TRUSTED AUTHORITY PLANE ─────────────────────┐
│                                                                  │
│  ┌──────────────┐       ┌──────────────────────────────┐          │
│  │ Identity /   │──────▶│ Contract + Effective Policy │          │
│  │ attestation  │       │ compiler                    │          │
│  │ SPIRE/WIF    │       └──────────────┬───────────────┘          │
│  └──────────────┘                      │                          │
│                                        ▼                          │
│                          ┌───────────────────────────┐             │
│                          │ Authorization monitors   │             │
│                          │                           │             │
│                          │ certification governor   │             │
│                          │ memory authority          │             │
│                          │ release controller        │             │
│                          │ effect authorizer         │             │
│                          └─────────────┬─────────────┘             │
│                                        │ one-use grant             │
│                                        ▼                          │
│                              ┌───────────────────┐                 │
│                              │ Runtime Tool     │                 │
│                              │ Broker           │                 │
│                              └──────┬────────────┘                 │
│                                     │                             │
│                 short-lived secret  │ trusted adapter             │
│                       ┌──────────────┴──────────────┐              │
│                       ▼                             ▼              │
│                Vault / cloud KMS             Effect adapter       │
│                                             GitHub/SaaS/DB/etc.   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ PostgreSQL authority state                                 │ │
│  │ grants · slots · operations · leases · policy versions     │ │
│  │ terminal decisions · invalidation head · signed ledger     │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                     │                    │                        │
│                     ▼                    ▼                        │
│              WORM evidence       Independent checkpoint witness  │
└──────────────────────────────────────────────────────────────────┘
                   ▲                       ▲
                   │ candidates/evidence   │ requests only
                   │                       │
═══════════════════╪════════════ TRUST BOUNDARY ═════════════════════
                   │                       │
┌──────────────────┴──── UNTRUSTED EXECUTION FABRIC ────────────────┐
│                                                                   │
│ Temporal workers       Agent runtime       NeMo Agent Toolkit      │
│ planners/builders      checklets           learned router          │
│                                                                   │
│ Frontier APIs          Nemotron/NIM        local open models       │
│ Switchyard             LiteLLM             Envoy/KServe            │
│ Dynamo replicas        vLLM/SGLang         embeddings/rerankers    │
│                                                                   │
│            ┌─────────────────────────────────────┐                │
│            │ Isolated arbitrary-code cells       │                │
│            │ Kata / gVisor / Firecracker         │                │
│            │ no creds · network deny · private FS│                │
│            └─────────────────────────────────────┘                │
└───────────────────────────────────────────────────────────────────┘

              DISTRIBUTION / OPERATIONS PLANE
       NATS · OTel · metrics · queues · caches · schedulers
```

This is intentionally stricter than common service-mesh architecture. A Kubernetes ServiceAccount name, pod label, `run_id`, HTTP header, environment variable, agent role name, or model-generated assertion is **not authority**. The workload proves an authenticated execution identity; the Core then resolves that identity to a principal and evaluates a separately frozen grant.

**What belongs in the TCB?** The narrow answer is the identity issuer/attestation mechanism, keys and KMS/HSM roots, the policy compiler and exact policy revision, the authorization monitors, broker, trusted effect adapters, authoritative database logic enforcing grant/effect cardinality, canonicalization/digest code, invalidation-freshness barrier, ledger signing/checkpoint machinery, and the isolation mechanism that prevents code cells from escaping their declared resource envelope. Kubernetes' control plane and host/hypervisor necessarily become part of the operational TCB where an administrator capable of replacing these components could bypass isolation or substitute trusted services.

**What does not need authority trust?** An LLM, Nemotron model, planner, researcher, verifier model, agent framework, learned router, Switchyard, model endpoint, inference scheduler, retrieval system, Temporal workflow worker, or an isolated code cell. These components can be compromised without being allowed to mint an `AuthorityGrant`. This follows directly from the Core's separation of `ExecutionCapability`, `ActionContract`, `AuthorityGrant`, and `ResourceHandle`. fileciteturn0file2

Temporal is especially useful here precisely because it **does not have to become the authority ledger**. Temporal persists workflow progress through event history and deterministic replay; its own architecture requires activities that have side effects to be idempotent or non-retryable because activity execution is not magically exactly-once. citeturn10search0turn10search1turn10search2 The Core should therefore let Temporal decide *that an activity needs another attempt* while forcing every consequential attempt through the broker. A compromised or duplicated Temporal activity can then cause repeated requests, but the effect slot prevents repeated authoritative commits.

The same principle applies to the event bus. JetStream provides durable consumers and at-least-once delivery, with optional message deduplication and double acknowledgements that improve perceived exactly-once semantics. Its own documentation nevertheless explains the failure scenarios that generate duplicates. citeturn17search1turn17search3turn17search7 **Therefore NATS should distribute invalidation events but not define whether an invalidation exists.** Store a monotonically increasing authoritative invalidation sequence in PostgreSQL; every event carries that signed sequence; and every authorization monitor proves that its consumed watermark is at least the current required head before committing.

That small modification is extremely important:

```text
Bad design:

NATS says "I have seen event 892"
        ↓
monitor trusts NATS
        ↓
authorize


Recommended design:

authoritative DB says required invalidation head = 892
                         │
NATS transports events  │
consumer watermark = 892│
                         ▼
monitor checks head == consumed/current
                         │
                         ├── yes → authorization may continue
                         └── no  → fail closed
```

The bus can now fail, duplicate messages, or recover from a snapshot without silently turning stale policy into fresh authority.

## Concrete component choices

The table below is the concrete 2026 decision matrix I would use.

| Surface | Recommended choice | Why it fits the Core | Strong alternatives | TCB status |
|---|---|---|---|---|
| **Workload identity** | **SPIRE/SPIFFE X.509-SVID** | Short-lived workload identity, process/workload attestation, mTLS and explicit trust-domain federation. citeturn18search0turn18search3 | EKS Pod Identity; GKE Workload Identity Federation; Azure managed workload identity | **Yes** |
| **Cloud credential bridge** | SPIFFE identity → cloud WIF/STS | Avoids long-lived service-account/API keys. GKE WIF explicitly issues short-lived external-cloud credentials and is recommended over exported service-account keys. citeturn16search0turn16search6 | Native cloud workload identity only | **Yes for effect principals** |
| **Semantic authorization** | **Cedar** in a Core-owned authorization service | Directly models principal/action/resource/context and supports schema validation; no matching permit defaults to deny. citeturn19search0turn19search11 | OpenFGA for very large relationship graphs; custom capability verifier | **Yes** |
| **Cluster/platform policy** | **OPA** | Excellent for admission/configuration/network/platform policy; supports signed bundles. citeturn19search13 | Kyverno, cloud policy services | Yes for cluster configuration, **not sole Core authority** |
| **Policy freshness** | Core DB revision + digest + invalidation barrier | OPA remote bundles are explicitly eventually consistent, so an OPA sidecar alone cannot prove the Core's required current watermark during a partition. citeturn20search0 | Central synchronous PDP | **Yes** |
| **Secret store** | **Vault** for hybrid installations | Dynamic secrets have leases and revocation; response wrapping supports short-lived single-use secret delivery. citeturn17search0turn17search6 | AWS Secrets Manager/KMS, GCP Secret Manager, Azure Key Vault | **Yes** |
| **Secret exposure pattern** | Broker fetches credential just-in-time; agent never receives it | Preserves Core's out-of-band grant/credential separation. Vault supports dynamic, leased credentials; GKE WIF likewise avoids static service keys. citeturn17search4turn16search6 | Sidecars only for trusted services | **Yes** |
| **Durable workflows** | **Temporal** | Durable replay, timers, task queues and activity retry semantics fit long-running graphs and human deferrals. citeturn10search1turn10search3 | AWS Step Functions, Azure Durable Functions, Google Workflows, Restate | **No effect authority** |
| **Authoritative DB** | **PostgreSQL 18** | Transactions, row locks, uniqueness and serializable transactions are enough for slots, grants, leases and terminal-state serialization. PostgreSQL 18 is the current supported release as of August 2026. citeturn21search7turn21search10turn21search12 | Cloud-managed PostgreSQL; globally serializable NewSQL only if truly necessary | **Yes** |
| **Event/invalidation distribution** | **NATS JetStream** | Lightweight durable fan-out, pull consumers and explicit ACK semantics. citeturn17search1turn17search3 | Kafka/Redpanda for much larger event/analytics footprints | Transport: **No**; authoritative head: **Yes** |
| **Artifact storage** | Content-addressed **S3-compatible** object storage | Object digest becomes artifact identity; S3 Object Lock gives versioned WORM retention where required. citeturn8search9 | Ceph RGW, MinIO-compatible deployment, GCS/Azure Blob immutability | Evidence preservation is trusted |
| **Authority ledger** | Append-only signed rows in PostgreSQL + hash/Merkle chain | Allows same transaction to serialize terminal decision and ledger event | Dedicated transparency-log system | **Yes** |
| **Independent ledger witness** | **Rekor-style transparency log** or separately administered WORM checkpoint | Rekor is append-only, cryptographically verifiable and supports external monitoring/witnessing; use it to witness checkpoint roots, not as the transactional state DB. citeturn9search3turn9search6 | Separate cloud/account WORM bucket + HSM signatures | **Yes to trust claim** |
| **Hostile arbitrary-code sandbox** | **Kata Containers** | Per-pod VM boundary while retaining Kubernetes scheduling semantics. Kata explicitly uses lightweight VMs/hardware virtualization rather than sharing the host kernel like ordinary containers. citeturn4search0turn4search2turn4search7 | Firecracker | **Yes** |
| **Lower-overhead code sandbox** | **gVisor** | Userspace application kernel and OCI runtime reduce direct host-kernel exposure while integrating with Kubernetes. citeturn3search12 | Nabla-like runtimes, WebAssembly for restricted languages | **Yes if used for declared isolation** |
| **Dedicated sandbox fleet** | **Firecracker** | KVM microVMs, minimal device model, Jailer and seccomp make it appropriate where you own an independent sandbox scheduler. citeturn3search0turn3search10 | Kata | **Yes** |
| **External-effect broker** | Custom Core service | `ActionContract → policy → reservation → grant → adapter → observation → reconciliation` is Core-specific and should not be outsourced to an agent framework. fileciteturn0file2 | None should replace the semantic broker |
| **Lease/locking** | PostgreSQL row + increasing fencing epoch | Exact external effect ownership must be validated at the state being mutated, not inferred from a timer | etcd lease/revision fencing for specialized coordination | **Yes** |
| **Distributed coordination** | etcd only where operationally useful | etcd's own docs warn that a lease/lock alone does **not** provide mutual exclusion for an external resource; the protected resource must validate a revision/fence. citeturn9search1 | Consul/ZooKeeper | Usually **No** |
| **Observability** | **OpenTelemetry** | Standard traces, metrics and logs across heterogeneous providers and runtimes. citeturn13search4 | Vendor-specific exporters behind OTel | **No** |
| **GPU provisioning** | **NVIDIA GPU Operator** | Automates driver, container toolkit, device plugin, node discovery, DCGM monitoring and related GPU stack. Current supported branch is 26.3.x. citeturn11search9turn11search16 | Cloud-managed GPU node images/operators | **No effect authority** |
| **GPU partitioning** | MIG for compatible production workloads; DRA as it matures in NIM integration | Kubernetes DRA itself is stable, but NVIDIA's NIM Operator documentation still labels its DRA integration a Technology Preview, so do not make NIM-DRA essential to the authority plane. citeturn13search9turn12search1 | Device Plugin + MIG Manager | No |

Two recommendations in this table deserve emphasis.

First, **Cedar and OPA serve different jobs**. Cedar maps unusually well onto the Reusable Core's semantic `principal/action/resource/context` authorization request. It also gives you a typed schema against which policies can be validated before activation. citeturn19search0turn19search2 OPA is excellent for Kubernetes admission, network configuration and broader infrastructure policy, but OPA's normal remote-bundle model is intentionally eventually consistent. citeturn20search0 Consequently, an OPA sidecar should not by itself be allowed to answer the question, “Is policy revision X definitely current immediately before this irreversible effect?”

Second, **never mount Vault/provider credentials into producer or sandbox pods** merely because Vault can rotate them. Vault's dynamic leases materially improve secret management, but once a bearer credential is readable inside an adversarial model/tool environment, the broker no longer completely mediates its use. citeturn17search6 Instead:

```text
agent
   │
   │ semantic request only
   ▼
broker
   │
   ├─ authenticate SPIFFE principal
   ├─ canonicalize parameters
   ├─ check frozen effective policy
   ├─ reserve effect slot
   ├─ mint one-use AuthorityGrant
   │
   ▼
trusted adapter
   │
   ├─ obtain short-lived provider credential
   ├─ perform exactly the approved operation
   └─ return receipt / observation

agent never sees provider credential
```

For isolated computation, there should also be a **hard physical separation between the agent's arbitrary code cell and GPU inference service**. Do not give the code sandbox a GPU merely because the model service needs one. NIM/vLLM lives on GPU worker nodes as a network service. Arbitrary generated shell/Python runs in a credential-free Kata/gVisor cell on a separate node pool. This shrinks both the GPU driver's attack surface exposed to generated code and the blast radius of a sandbox escape.

## NVIDIA and heterogeneous inference fabric

NVIDIA's 2026 software stack is useful here, but only when each component is assigned the correct architectural authority.

The NIM Operator now manages Kubernetes deployment and lifecycle for NIM and NeMo microservices, including model caches, services, autoscaling and integrations such as KServe. NVIDIA describes NIM as portable accelerated inference microservices and the NIM Operator as the Kubernetes lifecycle layer around them. citeturn12search4turn12search7 The GPU Operator separately manages the lower GPU software stack, including drivers, container runtime integration, device plugins and DCGM monitoring. citeturn11search9 These are excellent execution-plane components; neither should know anything about the Core's certification governor or `AuthorityGrant`.

NVIDIA Dynamo is a still lower inference-serving layer. Its router can use request/worker load and KV-cache overlap to choose inference workers, and NVIDIA provides Kubernetes deployment paths including integration with inference gateways. citeturn0search8turn0search11turn0search6 That solves a different optimization problem from the Core's semantic router.

The result should retain **three independent routing levels**:

```text
                    REUSABLE CORE
                         │
                         │ semantic / epistemic routing
                         │
                         ▼
             Which executor should do this?
     ┌────────────────────────────────────────┐
     │ cheap model │ Nemotron │ frontier API │
     │ specialist  │ local LM │ verifier     │
     └──────────────────┬─────────────────────┘
                        │
                        │ endpoint/provider routing
                        ▼
            MODEL GATEWAY / ABSTRACTION
     ┌────────────────────────────────────────┐
     │ Switchyard / LiteLLM / Envoy gateway  │
     │ cloud provider endpoint adapters       │
     └──────────────────┬─────────────────────┘
                        │
                        │ replica / KV / GPU routing
                        ▼
             INFERENCE SERVING LAYER
     ┌────────────────────────────────────────┐
     │ Dynamo │ KServe │ NIM │ vLLM │ SGLang │
     └────────────────────────────────────────┘
```

Your previous Nemotron research made essentially this distinction between agent/stage routing, model routing and replica/KV routing; that remains the right abstraction. fileciteturn0file1

**The Core-facing inference API should be yours.** Do not let application code import every provider SDK or bind semantic policy to Switchyard, LiteLLM, NIM or Bedrock-specific request types. Define something closer to:

```text
InferenceRequest
  run_id
  task_node_id
  execution_capability_id
  permitted_model_classes[]
  forbidden_model_classes[]
  residency_constraint
  data_classification
  context_manifest_digest
  max_input_tokens
  max_output_tokens
  latency_budget
  cost_budget
  retry_class
  route_policy_digest
  trace_context

InferenceResult
  logical_request_id
  attempt_id
  provider
  model_id
  model_version_or_revision
  endpoint_class
  serving_region_if_observable
  prompt_digest
  result_digest
  token_usage
  latency
  finish_reason
  provider_receipt
  route_reason
  fallback_chain[]
```

The model gateway can then be replaced without touching authority semantics.

**Switchyard is a strong conceptual fit but should remain replaceable.** NVIDIA's public implementation presents itself as a proxy capable of routing between heterogeneous model providers and OpenAI-compatible endpoints, with routing modes and telemetry. citeturn0search0 Your prior research also correctly treated it as a rapidly evolving component rather than the trusted foundation. fileciteturn0file1 Put it behind the stable interface above. Its route suggestion is an optimization decision, not authorization.

**LiteLLM is the pragmatic open-source alternative for provider normalization.** It exposes a common OpenAI-style interface across many providers and supplies load balancing, retries and fallbacks. citeturn14search0 That makes it useful as a provider adapter, but its generic retry/fallback policy must not be allowed to violate the Core's frozen model set, region restrictions or privacy policy.

**KServe has become a credible vendor-neutral local-serving alternative.** KServe v0.17 promoted `LLMInferenceService` to production readiness with KV-aware routing, disaggregated serving and distributed inference, and v0.18 added further multi-node and OpenAI Responses API capabilities. citeturn13search0turn13search13 Kubernetes' InferencePool API is stable and gives an Endpoint Picker visibility into metrics such as KV-cache utilization and queue depth. citeturn14search1 This is a natural open counterpart to Dynamo's inference-layer scheduling.

There is a maturity nuance here: the broader Gateway API Inference Extension project still describes portions of its getting-started experience as experimental even though `InferencePool` itself has graduated to a stable `v1` API. citeturn14search1turn14search4 So again: treat this as serving infrastructure, not a Core invariant.

**NeMo Agent Toolkit belongs inside producer/verifier activities rather than replacing Temporal or the Core.** NVIDIA's toolkit supports configurable event-driven workflow telemetry and OpenTelemetry exporters. citeturn11search1 That is useful for agent implementations, experiments and tracing. It does not provide the Reusable Core's exact-object authority protocol, effect slots or authority ledger.

The cloud-managed comparison is also important:

| Option | Strength | Core-specific problem |
|---|---|---|
| **AWS Bedrock** | Managed model portfolio plus cross-region inference profiles that can route among regions for capacity. citeturn15search0turn15search1 | Cross-region routing can move processing among predefined destination regions; Core policy must therefore decide whether that profile is compatible with residency requirements before invocation. |
| **Google Vertex AI** | Global and US/EU multi-region endpoints can dynamically route to available capacity; GKE WIF offers strong workload identity integration. citeturn16search2turn16search4turn16search6 | Hidden regional choice is acceptable only where the declared geographical set satisfies the effective policy. |
| **Microsoft Foundry** | Managed model router now spans multiple model families and includes built-in failover. citeturn15search2turn15search3 | Azure Policy restrictions can take time to propagate—the current documentation says up to fifteen minutes—so cloud policy cannot be the Core's immediate pre-commit freshness barrier. citeturn15search9 |
| **Self-hosted NVIDIA** | Maximum model/serving control, NIM optimization, Dynamo/KV routing, explicit GPU placement. citeturn12search4turn0search8 | You own availability, patching, capacity and GPU economics. |
| **Self-hosted OSS** | KServe/vLLM/SGLang and Envoy/Gateway APIs maximize vendor portability. KServe's 2026 releases materially improved production LLM serving. citeturn13search0turn13search13 | Integration effort is higher; no single project should inherit Core authority. |

The critical multi-provider rule is:

> **Fallback is permitted only inside a pre-authorized equivalence set.**

A generic gateway seeing `429` should not be free to turn:

```text
approved:
  Nemotron-local-US
  or Provider-A-US

into:

whatever responds fastest globally
```

Instead:

```text
Core route:
  allowed fallback set =
    {nim:nemotron-X:cluster-A,
     provider-A:model-Y:us}

Gateway:
  may choose only within that set

Nothing available:
  return unavailable

Core:
  decide whether to broaden route,
  defer,
  downgrade,
  or escalate
```

This is particularly important because current managed cloud inference products increasingly do their own cross-region/model routing. AWS documents that a Bedrock cross-region profile may route a request to any destination region within that profile; Google similarly uses regional pools for global or geographic endpoints. citeturn15search0turn16search2 Those are excellent availability features **after** the Core determines they are policy-compatible.

## Distributed semantics and failure-mode analysis

The hardest part of implementing v1.9 is not Kubernetes or GPUs. It is preserving its authority semantics under partial failure.

The Core already avoids claiming universal exactly-once effects. It models a semantic **effect slot** separately from transport operations, allows a maximum commit cardinality, and sends ambiguous outcomes to reconciliation rather than blind retry. fileciteturn0file2 That is the correct distributed-systems model.

The concrete implementation should make the linearization path roughly:

```text
BEGIN SERIALIZABLE

  lock effect_slot

  assert current_subject_digest
  assert current_policy_digest
  assert current_invalidation_head <= monitor_watermark
  assert lease.fencing_epoch == caller_epoch
  assert grant unused and unexpired
  assert operation parameters hash matches grant
  assert effect_slot committed_count < max_commits

  create operation_attempt(status = prepared)

COMMIT


perform provider operation
        │
        ├──────── success + receipt ────────┐
        │                                    │
        └──── timeout / connection loss ─┐   │
                                         │   │
                                         ▼   ▼
                                     reconcile
                                         │
                   ┌─────────────────────┼──────────────────┐
                   ▼                     ▼                  ▼
               not applied           applied           unknown
                   │                     │                  │
             retry permitted       record commit       STOP /
             same logical slot      once only          human/recheck
```

PostgreSQL transactions, row-level locks and unique constraints are appropriate for this type of serialization; PostgreSQL also supports serializable transactions where necessary. citeturn21search7turn21search12turn21search4

Do **not** use a Redis-style or etcd TTL lock as proof that the caller still owns the resource. The etcd documentation itself is unusually explicit on this point: lease expiration and clock differences mean lease ownership alone does not guarantee mutual exclusion for an external resource; correctness requires revision/version validation or an equivalent fencing mechanism at the protected resource. citeturn9search1 The Core's `validity epoch` maps naturally to such a fencing token.

The failure matrix is therefore:

| Failure | What naive architecture does | Required Core behavior |
|---|---|---|
| **Workflow worker crashes after requesting effect** | Retry whole tool call | Temporal may replay/retry, but broker sees same logical effect slot and joins/reconciles existing operation. Temporal itself requires side-effecting activities to handle retries safely. citeturn10search1 |
| **Provider commits but network response is lost** | Retry provider call | Mark `outcome_unknown`; query receipt or independently observe target; no new semantic intent merely because transport failed. fileciteturn0file2 |
| **Provider has no idempotency API and no read-after-write reconciliation** | Hope retry is safe | High-impact cardinality-one action should be marked unavailable for autonomous execution, or routed to human/manual reconciliation. |
| **NATS partition / missed invalidation** | Continue on local state | Compare local bus watermark with authoritative DB invalidation head; stale or unprovable freshness blocks governed transition. |
| **OPA sidecar has stale policy bundle** | Authorize with last bundle | OPA's bundle distribution is eventually consistent; Core authorization requires the frozen central policy revision/digest or fails closed. citeturn20search0 |
| **Policy update occurs after preliminary validation** | Commit using old decision | Final broker/controller recheck immediately before linearization, as v1.9 requires. fileciteturn0file2 |
| **Lease expires while worker continues running** | Old worker can still mutate | Every authoritative write carries fencing epoch; stale epoch fails even if worker believes it owns lease. |
| **Vault unavailable** | Use cached permanent credential | No new high-risk effect credential; defer/fail closed. Dynamic Vault secrets have explicit lease/revocation semantics. citeturn17search6 |
| **SPIRE unavailable** | Trust pod label/old identity forever | Existing SVID survives only to its validity boundary; authorization does not fall back to unverified identity. SPIFFE identities are issued through the Workload API and cryptographically validated. citeturn18search0turn18search3 |
| **Agent/code cell compromised** | Credential theft and lateral movement | Cell has no ambient credentials, no authoritative mounts and default-deny network; all exports reenter trusted validation/broker path. fileciteturn0file2 |
| **Sandbox escape** | Host compromise becomes full platform compromise | VM-backed Kata worker pool, separate from authority nodes and GPU serving; no authority secrets on sandbox nodes. Kata's VM boundary is stronger than ordinary shared-kernel containers, although it remains software requiring patch management. citeturn4search0turn4search7 |
| **Inference gateway compromised** | Gateway can choose arbitrary model/tool | Gateway can corrupt model output or consume inference budget but cannot mint effect grants; permitted model/residency envelope is signed/frozen upstream. |
| **Cheap-model router fails open** | Silently route to any model | Route broadening is a new Core decision, not an inference-gateway retry. |
| **Local GPU OOM/node failure** | Whole workflow fails | Inference attempt is retryable against another authorized replica/provider; no effect authority involved. Dynamo/KServe replica scheduling remains below semantic policy. citeturn0search8turn14search1 |
| **PostgreSQL loses quorum / authority store unavailable** | Continue from caches | Stop new governed transitions. Availability loss is preferable to split-brain authority. |
| **Ledger DB compromised retroactively** | Audit history silently changes | Signed hash/Merkle checkpoints are independently witnessed; Rekor-style logs provide append-only verifiability and third-party monitoring. citeturn9search3turn9search6 |
| **Object artifact overwritten under same path** | Verification points to different bytes | Authority refers to canonical content digest, not pathname. WORM/versioning is supplemental preservation, not artifact identity. S3 Object Lock protects object versions from deletion/overwrite during retention. citeturn8search9 |
| **Observability backend drops spans** | Missing trace interpreted as no event | OTel is operational telemetry, not proof of authorization or effect absence. Authority ledger and observations remain separate. OpenTelemetry's role is collection/export of traces, metrics and logs. citeturn13search4 |
| **Router or scheduler says “done”** | Workflow terminates | Terminal disposition still requires registered Core transition and applicable monitor. fileciteturn0file2 |

There is an important architectural benefit hidden here: **Temporal does not need to be in the effect TCB**. NATS does not need to be the authority source of truth. Switchyard does not need to be trusted. The inference gateway does not need effect credentials. The LLM obviously does not need authority. Even most verifiers need no mutation authority.

That gives you a sharply reduced compromise graph:

```text
COMPROMISE                 EXPECTED MAXIMUM DAMAGE

LLM                         bad candidate / malicious request
Agent                       bad requests / compute burn
Router                      misrouting / compute burn
Verifier                    bad evidence recommendation
Switchyard                  inference corruption / data exposure
Inference server            model corruption / availability
Temporal worker             duplicate requests / workflow corruption
NATS                        delay / duplicate / suppress notifications
OTel collector              telemetry loss/corruption
Sandbox process             private-cell compromise

                              │
                              │ still cannot authorize effect
                              ▼

Broker / Authorization Monitor / Identity root / Authority DB
                              │
                              ▼
                     THESE are the critical TCB
```

The design goal is not to make the upper components harmless. A compromised model gateway can still leak prompts or incur substantial cost. It is to prevent those compromises from automatically becoming **effect-authority compromise**.

## Deployment progression and minimal demonstrator

The deployment should grow by **preserving interfaces and increasing physical separation**, not by rewriting architecture at each stage.

| Stage | Concrete installation | What it proves |
|---|---|---|
| **Laptop / workstation** | Single-node Linux Kubernetes or k3s; PostgreSQL; NATS JetStream; Temporal; MinIO/S3-compatible store; Vault dev/test deployment; Cedar library/service; Core broker; two mock inference endpoints; gVisor where supported | Contracts, digests, policy composition, grants, effect slots, operation reconciliation, invalidation watermark, no-agent-credentials rule |
| **Single GPU server** | Same control plane plus NVIDIA GPU Operator, local NIM or vLLM, a Core inference gateway, separate CPU sandbox runtime | Cheap/local vs frontier routing, local Nemotron/NIM serving, GPU telemetry, network separation between inference and arbitrary code |
| **Private cluster** | HA Kubernetes; dedicated authority/control node pool; Kata sandbox node pool; GPU inference node pool; HA PostgreSQL; SPIRE; Vault; Temporal Cloud or HA Temporal; 3-node JetStream; object store; checkpoint witness; GPU/NIM Operators; Dynamo or KServe as scale requires | Principal separation, node-level blast-radius reduction, replicated workflow/event infrastructure, real sandboxing, independent ledger witness, production failure recovery |
| **Hybrid multi-cloud** | One authoritative home control plane plus regional/cloud execution planes; SPIFFE trust-domain federation; cloud WIF; local model gateways; replicated content-addressed artifacts/evidence; signed invalidation stream; provider-specific inference adapters | Heterogeneous providers, residency-aware routing, cloud outage tolerance, no shared static cloud keys, remote execution without remote sovereign authority |
| **Optional global authority later** | Only after necessity is demonstrated: globally consistent replicated authority DB and geographically separate monitors/witnesses | Active-active governed transitions, at the cost of a substantially larger TCB and much harder failure analysis |

The **single biggest deployment recommendation** is not to begin with active-active multi-cloud authority. In the initial hybrid architecture, clouds should be **federated execution zones**, not co-equal sovereign control planes:

```text
                       AUTHORITY HOME
                 ┌────────────────────────┐
                 │ policy / broker / DB   │
                 │ governors / ledger     │
                 └──────────┬─────────────┘
                            │
             signed tasks / │ candidates / evidence
                            │
        ┌───────────────────┼────────────────────┐
        ▼                   ▼                    ▼
 AWS execution zone    private GPU zone    GCP/Azure zone
 Bedrock               NIM/Nemotron         Vertex/Foundry
 local models          Dynamo/KServe        cloud models
 sandboxes             sandboxes            sandboxes
```

SPIFFE federation is explicitly designed to exchange trust bundles across trust domains. citeturn18search0 Cloud workload identity can then bridge a particular federated workload into local cloud IAM without distributing permanent cloud credentials. GKE, for example, recommends Workload Identity Federation and issues short-lived access from Kubernetes identities rather than requiring exported service-account keys. citeturn16search0turn16search6

This topology also simplifies disaster semantics. If a cloud execution zone disappears, you lose capacity. If the authoritative home plane loses quorum, you lose permission to create new consequential state. That failure mode is much easier to reason about than two disconnected regions both believing they are authorized to send the same payment, message, repository push or release.

**A genuinely minimal end-to-end Reusable Core demonstrator** does not need every technology in the final matrix. I would build this first:

```text
single-node k3s / Kubernetes

Trusted:
  core-api
  policy-compiler + Cedar
  certification-governor
  runtime-broker
  mock-effect-adapter
  PostgreSQL
  Vault
  SPIRE server/agent

Semi-trusted infrastructure:
  Temporal
  NATS JetStream
  MinIO
  OTel Collector

Untrusted:
  cheap-model worker
  frontier-model worker
  verifier worker
  isolated code worker
```

Use **mock model endpoints before any paid frontier integration**, because the first research question is not whether a model can reason. It is whether the runtime preserves invariants when its participants misbehave.

The initial acceptance suite should mechanically demonstrate approximately these cases:

| Experiment | Required result |
|---|---|
| Producer directly calls effect provider | Network path/credential unavailable |
| Producer fabricates `role=release_controller` | Authentication resolves actual SPIFFE principal; claim ignored |
| Producer requests valid action outside resource scope | Cedar/Core authorizer denies |
| Agent obtains shell in code cell | No broker/Vault/provider credential visible |
| Code cell attempts internet egress | Denied except named mediated reads |
| Same logical effect requested twice | Exactly one effect slot; second request joins/rejects rather than creating intent |
| Broker crashes immediately before provider call | Operation remains prepared; safe restart |
| Broker crashes after provider commits but before receipt saved | `outcome_unknown`; reconciler observes provider before deciding retry |
| Parameters change while reusing operation ID | Idempotency conflict |
| Artifact changes after verification | Previous verdict/certificate unsupported for new digest |
| Policy changes between initial decision and commit | Final recheck fails stale policy digest |
| Invalidation message withheld from monitor | DB head exceeds monitor watermark; transition blocks |
| Lease expires while old controller runs | Old fencing epoch rejected |
| NATS sends same invalidation twice | Idempotent application of sequence |
| Temporal replays effect activity | Broker effect slot prevents duplicate semantic commit |
| Router selects disallowed provider/model | Model gateway rejects route envelope |
| Verifier attempts candidate mutation | Identity/action policy denies |
| Test environment attempts production ledger append | Production identity/credential unavailable |
| Authority ledger record altered retrospectively | Hash/checkpoint verification fails |
| External checkpoint witness unavailable | Protected transition follows declared fail-closed/staleness policy |

That demonstrator tests far more of v1.9 than connecting ten LLMs would.

Once that works, add the single-GPU execution fabric. NVIDIA's GPU Operator automates the host GPU software stack, while the current NIM Operator manages NIM/NeMo deployments, caches and autoscaling. citeturn11search9turn12search4 A local Nemotron-class endpoint can then be just another `ExecutionCapability`.

Only after those pieces exist should sophisticated learned routing become important—exactly in line with v1.9's own implementation dependency ordering, which puts typed artifacts, deterministic gates, identity/policy/ledger/invalidation, broker isolation and effect reconciliation before learned routing. fileciteturn0file2

## Normative compatibility and implementation gaps

I found **no fundamental contradiction that requires redesigning Reusable Core v1.9**. I did find several places where the abstract contract forces non-obvious concrete implementation choices.

**Invalidation freshness necessarily sacrifices availability during certain partitions.** There is no distributed implementation that can both prove “I have observed every causally relevant revocation up through the current authoritative head” and remain independently writable during an arbitrary partition without additional assumptions. This is not a contradiction because v1.9 already says consequential transitions fail closed on stale or unprovable invalidation state. fileciteturn0file2 The concrete consequence is that the invalidation watermark must be tied to an authoritative monotonic head, not merely “latest message I happened to receive.”

**Universal at-most-once external effects are impossible for arbitrary provider APIs.** A provider that offers neither a stable idempotency key nor an independently queryable receipt/state can leave the broker unable to distinguish “request did not happen” from “request happened but response was lost.” Again, v1.9 already models `outcome_unknown` and explicitly rejects a universal exactly-once claim. fileciteturn0file2 The deployment rule should therefore be stronger: a high-impact action whose provider cannot support adequate reconciliation is **not an eligible autonomous action contract**.

**An independent effect observation is not always technologically available.** For Git repository operations you can reread the remote ref; for messages you may have a provider message ID; for payment APIs you may query transaction state. For some legacy systems there is no independent observation channel. The Core's existing “capability unavailable rather than silently downgraded” principle should apply. fileciteturn0file2

**OPA's ordinary distribution model cannot alone instantiate the Core's policy-freshness semantics.** OPA explicitly describes remote policy/data bundles as eventually consistent. citeturn20search0 This is an implementation mismatch, not a Core contradiction. The remedy is to use OPA as a platform policy engine while binding consequential authorization to an exact Core-owned effective-policy digest and authoritative current revision.

**Temporal's workflow history is not the authority ledger.** Temporal's history is excellent for reconstructing workflow execution state through event sourcing and replay. citeturn10search0turn10search2 But it should not be treated as evidence that an effect was authorized or as the linearization record for the Core. That belongs in the broker/authority transaction plus independently witnessed ledger.

**A single laptop cannot prove physical principal independence.** Separate processes and keys can demonstrate the protocol, but the same administrator/root/kernel can compromise all of them. That is acceptable for the minimal demonstrator; production claims about independent monitors, witness keys and sandbox containment require genuinely separated credentials, namespaces/nodes and—in the strongest cases—administrative domains.

**A transparency log does not replace transactional authority state.** Rekor is designed as an immutable, append-only, cryptographically verifiable transparency log and supports independent monitoring. citeturn9search3turn9search6 It is an excellent *witness* for signed authority-ledger checkpoint roots. It is not the right place to perform effect-slot transactions, row locks or policy-state coordination. That stays in PostgreSQL.

**WORM storage does not define artifact identity.** S3 Object Lock preserves protected versions under retention; it does not prevent a different object version from being created under the same logical key. citeturn8search5turn8search9 Therefore v1.9 is correct to bind authority to canonical digests rather than paths, filenames or mutable object-store pointers.

**Cloud-native model routers can violate observability or residency assumptions unless constrained outside themselves.** Bedrock cross-region profiles explicitly route among destination regions, while Vertex global/multi-region endpoints dynamically select capacity across their declared geography. citeturn15search0turn16search2 These are perfectly compatible with the Core only when their entire possible routing envelope is acceptable under the effective policy. A hidden router that may choose a prohibited model or jurisdiction is not a valid implementation of a frozen Core route.

**NVIDIA DRA should not yet be a hard dependency of this architecture.** Kubernetes core DRA is stable, but NIM Operator's current DRA integration remains marked Technology Preview and unsuitable for production in NVIDIA's own documentation. citeturn13search9turn12search1 Use mature GPU Operator/device-plugin/MIG paths today where required, while designing the scheduling abstraction so DRA can replace them later.

The resulting architecture can be summarized in one dependency graph:

```text
                       APPLICATION / DOMAIN PACKS
                                  │
                                  ▼
                        ┌───────────────────┐
                        │  REUSABLE CORE    │
                        │                   │
                        │ contracts         │
                        │ graph semantics   │
                        │ verification      │
                        │ routing policy    │
                        │ certification     │
                        │ memory governance │
                        └─────────┬─────────┘
                                  │
              ┌───────────────────┴──────────────────┐
              │                                      │
              ▼                                      ▼
     TRUSTED AUTHORITY MICROKERNEL            EXECUTION FABRIC
                                                 (untrusted)
 identity / SPIRE                           Temporal activities
 policy compiler / Cedar                    agents
 broker / adapters                          Nemotron
 exact-object monitors                      frontier APIs
 Vault/cloud IAM                            NIM
 authority PostgreSQL                       Dynamo
 invalidation freshness                     KServe
 ledger + witness                           vLLM/SGLang
 sandbox enforcement                        Switchyard/LiteLLM
                                            checklets
              │                             learned routing
              │                                      │
              └───────────────────┬──────────────────┘
                                  ▼
                           Kubernetes / compute
                     CPU nodes │ sandbox nodes │ GPUs
```

The architectural judgment I would make most strongly is therefore:

> **Do not make the agent orchestrator, model router, workflow engine, inference gateway, event bus, or NVIDIA software stack the root of trust.**

Make them **clients of a much smaller authority kernel**.

The best version of this system is one in which Nemotron, a frontier API, Temporal, Switchyard, NIM, Dynamo, the agent framework, the event bus and even the verifier layer can all be independently replaced without changing the meaning of:

```text
Who is this principal?
What exact artifact is being acted upon?
Which effective policy applies?
What evidence currently supports the transition?
Has anything invalidated that evidence?
Which exact action and resource are permitted?
How many authoritative effects may occur?
Has this semantic effect already happened?
Who is allowed to linearize the transition?
Can we independently demonstrate what happened afterward?
```

Those questions are the durable architecture.

Everything else is compute.

That separation is not only compatible with Reusable Core v1.9; it is the concrete infrastructure interpretation that makes its central thesis—**agents are optional implementation strategies, while artifacts, verification, authority and total-path evidence are durable**—actually enforceable in a heterogeneous 2026 deployment. fileciteturn0file2