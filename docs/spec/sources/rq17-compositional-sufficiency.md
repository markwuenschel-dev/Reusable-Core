> **Reusable Core v1.10 — Source: RQ17 compositional sufficiency report**
>
> NON-normative source research (COMPOSITION). Adopted into kernel §12 and Volume II §10.10–§10.11.
>
> **Precedence:** the [v1.10 kernel](../reusable-core-v1.10-kernel.md) wins any conflict with this document. Internal references to "v1.9" and to sibling documents by their former names are historical; see the [supersession map](../README.md#supersession-map).
>
> **Fidelity:** everything below the end-of-header marker is the source document reproduced byte-for-byte (`Compositional_Sufficiency_Across_Spines_and_Domain_Packs.md`, SHA-256 `8a3f5e87f35ce0c2`).

<!-- v1.10 volume header end -->
# RQ17 — Compositional Sufficiency Across Spines and Domain Packs

## TL;DR
- **Independent validation is sufficient only inside a narrow "safe compositionality envelope": disjoint mutable state (robust partitioning / separation-logic frame), acyclic or well-founded assume-guarantee dependencies, attenuated/disjoint authority, and statistically independent evidence bases. Outside that envelope, composition is provably NOT free — non-interference, hyperproperties, probabilistic claims, and policy combinations are all known to break under composition — so interaction-aware (joint) certification is the default, not the exception.**
- **The literature treats three things differently and RQ17 must too: PROPERTY composition (sometimes theorem-backed, e.g. Mantel's MAKS, interface-automata independent implementability, the UC composition theorem, ARINC-653+DO-297), EVIDENCE composition (essentially never multiplicative when sources are shared — Knight–Leveson, Littlewood–Rushby), and CERTIFICATE/ARGUMENT composition (standardized practice via DO-297 incremental acceptance, ISO 26262 SEooC/AoU, modular GSN contract modules — but these are disciplined bookkeeping, not proofs).**
- **Actionable output below: a four-channel taxonomy (dependency, evidence-sharing, state-sharing, authority-overlap) with exact preconditions; a checkable TRIGGER PREDICATE for joint certification; a graded L0–L3 certification ladder grounded in DO-297; and a YAML pack-interaction schema. The single most important design move is to buy composability by construction (partitioning + object-capability attenuation + append-only content-addressed facts + a single serializing Authorization Monitor) so that most pack pairs stay at L0/L1.**

## Key Findings

1. **Composition is non-compositional by default for exactly the property classes assurance certificates care about.** Noninterference and its generalizations are provably not preserved under composition (McCullough 1988; McLean 1994); hyperproperties (Clarkson & Schneider 2008/2010) resist compositional reasoning because they are sets of trace-sets and cannot be checked one trace at a time; probabilistic/quantitative claims do not compose by conjunction (they require joint-distribution or multi-objective reasoning — Kwiatkowska et al. 2013); and access-control safety is undecidable in the general case (HRU 1976). Any RQ17 rule that assumes "independently valid ⇒ jointly valid" is unsound unless it discharges specific preconditions.

2. **There ARE genuine sufficiency theorems, but each charges a precise price.** Interface automata give "independent implementability" (de Alfaro & Henzinger 2001); contract-based design gives independent implementability when composition is monotone w.r.t. refinement (Benveniste et al. 2018); Mantel's MAKS generalized zipping lemma (2002) gives sufficient conditions under which BSPs compose; the Universal Composability theorem (Canetti 2001) preserves security under arbitrary concurrent composition — but only with trusted setup and with joint state handled explicitly (Canetti–Rabin JUC 2003). Circular assume-guarantee needs a well-foundedness/"next-time" discharge to be sound (Abadi–Lamport, McMillan, Namjoshi–Trefler).

3. **Industrial certification standards already encode the RQ17 answer as disciplined practice, not theorem.** DO-297/ARINC 653 make robust time-and-space partitioning the *precondition* that licenses incremental acceptance; ISO 26262 SEooC discharges Assumptions of Use at integration and uses Freedom-From-Interference + Dependent Failure Analysis to justify coexistence; modular GSN uses away-goals and contract modules to bind module arguments. All three explicitly forbid modular credit at the top integration level — i.e., they *mandate* a joint step.

4. **Evidence never multiplies when sources are shared.** Knight & Leveson ("An Experimental Evaluation of the Assumption of Independence in Multiversion Programming," IEEE TSE SE-12(1):96–109, 1986) prepared 27 versions independently from the same specification at two universities and subjected them to one million tests; of the 24 versions with nonzero failure rates, coincident failures significantly exceeded the independence prediction. A 2026 replication — "N-Version Programming with Coding Agents" (ASSERT-KTH, arXiv:2606.20158), using 69 coding agents across 5 harnesses (Cursor, Claude Code, OpenAI Codex, Gemini, OpenCode) on the Launch Interceptor Program spec — reproduced it exactly: "Across the 48 admitted implementations in the campaign archive, the experiment produces 429 coincident-failure cases where the independence model predicts 115.36." Littlewood & Rushby's possible-perfection work shows even a 1-out-of-2 diverse channel pair is not statistically independent. Two pack certificates resting on the same verifier, corpus, simulator, or base model do not give the product of their individual assurance.

5. **The four RQ17 channels map cleanly onto four literatures with different maturity:** dependency → assume-guarantee/contracts (mature, theorem-backed); state-sharing → separation logic/partitioning (mature, theorem-backed); authority-overlap → object-capability/policy-algebra/HRU-safety (mature but with undecidability walls); evidence-sharing → common-cause/diversity literature (empirical, quantitative but no clean composition theorem). LLM-agent specifics (confused deputy, guardrail layering, AI-control protocols) are the least mature and mostly heuristic.

## Details

### A. The compositional sufficiency problem in this setting — three distinct questions

For Core spine `S` and domain packs `P₁…Pₙ`, "can independently validated artifacts compose without joint certification?" is really three questions the literature answers differently:

**(i) Property composition** — does `S ∥ P₁ ∥ … ∥ Pₙ` satisfy the conjunction of the pack-local guarantees? This is the assume-guarantee / interface-theory / information-flow-composition question. *Sometimes* theorem-backed; often false.

**(ii) Evidence composition** — if each certificate carries a confidence/probability, what confidence attaches to the composite? This is the statistical-independence / common-cause question. Almost never multiplicative under shared sources; there is no general composition theorem, only correlation accounting.

**(iii) Certificate/argument composition** — can the *assurance arguments* be linked without re-arguing? This is the modular-safety-case / incremental-acceptance question. Standardized practice (DO-297, ISO 26262 SEooC, modular GSN) — but these frameworks are bookkeeping disciplines that *depend on* (i) and (ii) holding; they do not substitute for them.

**PROPOSED (report's own framing):** The RQ17 conflation risk is that a registry might treat a green "certificate composes" flag as if it answered all three. It does not. A pack pair can pass (iii) (arguments link syntactically) while failing (i) (a shared-state interaction violates a guarantee) or (ii) (both certificates rest on the same red-team corpus). The trigger predicate in §D must therefore fire on all three independently.

### B. Taxonomy of the four interaction channels

#### B.1 DEPENDENCY (pack A's guarantee relies on pack B's / the spine's behavior)

*Formal home:* assume-guarantee (Jones' rely-guarantee 1983; Chandy–Misra), contract-based design (Benveniste et al. 2018), interface theories (de Alfaro–Henzinger 2001).

- **Sufficiency condition (PROVEN).** If dependencies form a DAG and each component satisfies its contract `C_i = (A_i, G_i)` with the discharge `G_j ⇒ A_i` for every edge j→i, then the composite satisfies the conjunction — *non-circular* assume-guarantee is sound by transitivity (Namjoshi–Trefler formalize this: "soundness follows immediately from P1 and the transitivity of ⇒"). Benveniste et al.: parallel composition of contracts "supports independent development, meaning composing legal implementations for each subcontract yields a legal implementation for the system-level contract" — but note only *refinement*, not equality, holds for multi-viewpoint conjunction (their Property 6).
- **Failure mode.** *Cyclic* dependencies (A assumes B, B assumes A). Naïve circular reasoning is unsound. Maier's result: sound circular assume-guarantee rules cannot be complete, and complete rules must use auxiliary assertions. Circular rules become sound only with a well-founded discharge — a "next-time" operator or a safety-closure induction (Abadi–Lamport 1995 "Conjoining Specifications"; McMillan's circular rule; Namjoshi–Trefler's Circular Reasoning II adds hypothesis (e), a safety-closure check). For continuous/interconnected systems the analogue is: weak contract satisfaction suffices for DAG interconnections, strong satisfaction is needed for cycles (Saoud et al., *Automatica* 2021).
- **Independent-implementability precondition (PROVEN, interface automata).** de Alfaro–Henzinger interface automata are *optimistic*: two interfaces are compatible if there *exists* an environment making them work, and refinement (alternating simulation) preserves compatibility, giving independent implementability. Modal interfaces and Larsen's work add conjunction. The precondition is input/output determinism of the interface and that refinement is contravariant on inputs.
- **Mitigation:** contract refinement + acyclicity check; where cycles are unavoidable, require an explicit well-founded discharge artifact.

#### B.2 STATE-SHARING

*Formal home:* separation logic / concurrent separation logic (O'Hearn, Brookes), the frame rule; robust partitioning (ARINC 653).

- **Sufficiency condition (PROVEN).** The **frame rule**: `{P} C {Q} ⊢ {P∗R} C {Q∗R}` provided `mod(C) ∩ fv(R) = ∅`. Concurrent separation logic: `{P₁}C₁{Q₁}  {P₂}C₂{Q₂} ⊢ {P₁∗P₂} C₁∥C₂ {Q₁∗Q₂}` — independent reasoning is sound *iff the footprints are disjoint* (separating conjunction ∗). Ownership can transfer dynamically but must be disciplined (O'Hearn's pointer-transferring buffer).
- **Failure mode.** Shared *mutable* state outside a declared frame. If pack A writes state that pack B's guarantee reads and B did not declare it in its assumption, B's certificate is void. This is the exact Knight Capital mechanism (below): SMARS distributed orders across servers "assuming that each server operated under identical logic"; one server ran a repurposed dormant flag → divergent shared state → catastrophic loss.
- **Mitigation (STANDARDIZED PRACTICE).** ARINC 653 robust time-and-space partitioning; DO-297 makes robust partitioning ("demonstrable means of containment, protection and enforcement of the partition boundaries" — AC 20-170 glossary) the *enabling precondition* for incremental acceptance. ISO 26262 Freedom From Interference (FFI): "the absence of cascading failures … used to justify coexistence of elements," established via Dependent Failure Analysis over shared resources (clock trees, memory, buses).

#### B.3 AUTHORITY-OVERLAP

*Formal home:* object-capability model (Miller, *Robust Composition* 2006), policy algebras (Bonatti et al. 2002), HRU safety (1976), ARBAC safety (Li–Tripunitara).

- **Hard limit (PROVEN).** The HRU safety problem — "can right r be leaked to an unintended subject?" — is *undecidable* in general (reduction from Turing-machine halting); decidable but NP-complete for mono-operational systems; undecidable for biconditional monotonic systems; decidable for monoconditional monotonic. So "can overlapping authority grant an unintended permission" is not answerable in general — you must restrict the model.
- **Sufficiency condition (PROVEN, object-capability).** Miller: "only connectivity begets connectivity"; authority is bounded by the reference graph. If packs receive authority only by explicit delegation and attenuate it via membranes/access-abstractions, then "diverse expressions of policy often compose correctly even when none of the interested parties are aware this is happening" (Miller §11.4). The precondition is no ambient authority: authority must be carried by the invoker, not held ambiently (Hardy's confused-deputy insight, 1988).
- **Policy-combination sufficiency (PROVEN/algebraic).** Bonatti–di Vimercati–Samarati give an algebra of access-control policies with formal semantics; composition is well-behaved when the combining operators are used with known algebraic properties. Per the OASIS "eXtensible Access Control Markup Language (XACML) Version 3.0" standard (OASIS Standard, 22 Jan 2013), the standard rule/policy combining algorithms are deny-overrides, permit-overrides, first-applicable, only-one-applicable, ordered-deny-overrides, ordered-permit-overrides, and (added in 3.0) deny-unless-permit and permit-unless-deny. These *resolve* conflicts at decision time but do not *detect* them, and known anomalies (conflict, redundancy, incompleteness) persist — static analysis (Margrave, SAT/SMT encodings) is needed. **Order-dependent algorithms (e.g., first-applicable, ordered-*-overrides) mean the composite policy depends on pack load order** — a composition hazard.
- **Failure mode.** Confused deputy at a shared tool surface: a pack holding a credential is redirected by injected content to act for another principal. 737 MAX MCAS is the canonical authority-overlap safety failure: a function given control authority keyed off a single AoA sensor, able to override, without the integration-level analysis of that authority's interaction with the pilot control loop.
- **Mitigation:** capability attenuation, disjoint authority sets, provenance-bound authorization (authority scoped to request origin), and a single serializing Authorization Monitor (the user's v1.8 pattern) as the reference-monitor composition point.

#### B.4 EVIDENCE-SHARING

*Formal home:* common-cause/common-mode failure, beta-factor models, Knight–Leveson, Littlewood–Rushby, Bloomfield–Rushby Assurance 2.0.

- **Core negative result (EMPIRICAL, strongly replicated).** Independent development does NOT yield independent failures. Knight & Leveson (IEEE TSE SE-12(1):96–109, 1986): coincident failures far exceeded the independence prediction across 27 independently-developed versions under one million tests. Eckhardt–Lee and Littlewood–Miller: shared specifications and shared developer background create positively correlated failure modes as a matter of principle. The 2026 coding-agent replication (arXiv:2606.20158) found 429 coincident-failure cases where independence predicted 115.36.
- **No composition theorem exists.** There is no sound way to multiply two certificates' probabilities when their evidence bases overlap. Littlewood–Rushby: even a 1-out-of-2 diverse system's channels are not independent; conservative Bayesian inference is required, and claims of "possible perfection" for one channel must be argued, not assumed.
- **Confidence discipline (STANDARDIZED-ish).** Bloomfield & Rushby Assurance 2.0 / eliminative argumentation (Goodenough–Weinstock–Klein defeaters): confidence comes from *eliminating defeaters*, and correlated evidence in an assurance BBN does not raise confidence the way independent evidence would.
- **Mitigation (PROPOSED):** evidence-provenance tagging on every certificate (verifier ID, corpus hash, simulator version, base-model ID) and a correlation check that refuses to multiply confidences whose provenance sets intersect above a threshold.

### C. Sufficiency theorems / rules — strongest defensible statements

**T1 (Non-circular A-G, PROVEN).** If the pack/spine dependency graph is acyclic and every contract discharge `G_j ⇒ A_i` holds along edges, then pack-local guarantees compose to their conjunction without joint certification. *Precondition:* acyclicity; contracts are safety (or liveness with safety-closure handling).

**T2 (Circular A-G, PROVEN with cost).** Circular dependencies compose soundly only with a well-founded discharge (next-time induction or safety-closure check à la Namjoshi–Trefler Circular Reasoning II / McMillan). *Precondition:* the extra soundness hypothesis; not complete without auxiliary assertions (Maier).

**T3 (Interface-automata independent implementability, PROVEN).** If pack interfaces are modeled as interface automata and each implementation refines its interface (alternating simulation), compatible interfaces remain compatible under refinement → packs are independently implementable. *Precondition:* optimistic compatibility (an accommodating environment exists); I/O interface discipline.

**T4 (Contract independent implementability, PROVEN).** Parallel composition monotone w.r.t. refinement ⇒ composing legal implementations yields a legal implementation of the composed contract (Benveniste et al. 2018). *Precondition:* base components monotone; only refinement (not equality) for multi-viewpoint conjunction.

**T5 (Frame / CSL disjointness, PROVEN).** Disjoint footprints (`∗`) ⇒ thread/pack-local proofs compose. *Precondition:* `mod(C) ∩ fv(R) = ∅`; disciplined ownership transfer.

**T6 (MAKS composition, PROVEN with conditions).** Mantel's generalized zipping lemma ("On the Composition of Secure Systems," IEEE S&P 2002) gives sufficient conditions under which basic security predicates (BSPs) — hence information-flow properties built from them — are preserved under composition. *Precondition:* the specific BSP-dependent side conditions; restrictiveness-style properties compose, weaker ones (generalized noninterference) do not in general (McCullough; McLean).

**T7 (UC composition, PROVEN with heavy price).** UC-realizing an ideal functionality lets a protocol be substituted into any environment preserving security under arbitrary concurrent composition (Canetti 2001). *Precondition:* trusted setup (CRS / CA) is required — bit commitment and general MPC are impossible in the plain model (Canetti–Fischlin); joint state must be handled by JUC (Canetti–Rabin 2003) because standard UC assumes disjoint state and independent randomness.

**T8 (Probabilistic A-G, PROVEN, does NOT reduce to conjunction).** Kwiatkowska et al. ("Compositional probabilistic verification through multi-objective model checking," *Information and Computation* 232:38–65, 2013): compositional verification of probabilistic automata is possible but via *multi-objective model checking*, not conjunction of scalar probabilities; parallel composition of PAs is associative and commutative, and quantitative guarantees compose only through the multi-objective machinery and often only under fairness. *Precondition:* the assumption-probability arithmetic, fairness for quantitative (non-safety) properties.

**T9 (ARINC 653 + DO-297 incremental acceptance, STANDARDIZED PRACTICE).** Robust time-and-space partitioning ⇒ modules and applications may be accepted independently (DO-297 Task 1 Module Acceptance §4.2, Task 2 Application Acceptance §4.3) and reused (Task 6 §4.7) — but *only within the declared Usage Domain* ("an exhaustive list of conditions … to be respected by the user(s) to ensure that the IMA module continues to meet its characteristics" — EASA ETSO-C153a), and *no modular credit is granted at Task 3 (IMA System Acceptance §4.4) or Task 4 (Aircraft Integration §4.5)* — AC 20-170 §4-2: "We do not allow reuse of previously accepted data at the IMA system level (Task 3 …) or IMA installation level (Task 4 …)." Integration verification of resource allocation, partitioning, and health-monitoring is mandatory. *This is the industrial template for the graded ladder in §E.*

**T10 (ISO 26262 SEooC AoU discharge, STANDARDIZED PRACTICE).** An element developed out of context is composable into an item iff its Assumptions of Use are verified against the item's safety requirements at integration, and FFI is established via Dependent Failure Analysis (ISO 26262-9). *Precondition:* AoU completeness; DFA covers shared resources/coupling factors.

**No-theorem zones (be explicit):** (a) evidence composition — only correlation accounting, no theorem; (b) hyperproperty composition in general (Clarkson–Schneider) — refinement does not even preserve them (refinement paradox); (c) authority-leakage in general (HRU undecidable); (d) LLM-agent guardrail-layer composition — heuristic only (defense-in-depth is an engineering posture; vendor guidance itself states guardrails "cannot guarantee complete safety").

### D. TRIGGER PREDICATE for interaction-aware (joint) certification

Joint certification is REQUIRED if **any** of the following holds over the pack/spine registry (encodable as a lint rule):

1. **Shared mutable state outside a declared frame:** ∃ state cell written by one pack and read by another (or by the spine) not covered by both parties' declared assumption frames (violates T5).
2. **Cyclic dependency without a well-founded discharge:** the import/export graph has a cycle and no pack in the cycle provides a next-time/safety-closure discharge artifact (violates T1; T2 not satisfied).
3. **Undischarged contract edge:** ∃ edge j→i where `G_j ⇒ A_i` is not established (violates T1/T4).
4. **Authority union crosses a harm-tier boundary:** the union of two packs' authority sets enables an action in a higher lexicographic harm tier than either pack alone (authority-overlap; cf. HRU leakage — since general detection is undecidable, treat any union that touches a higher tier as a trigger).
5. **Shared tool surface with ambient authority:** two packs invoke a common tool/credential without per-invocation, provenance-bound authorization (confused-deputy risk).
6. **Correlated evidence above threshold:** two certificates' evidence-provenance sets (verifier, corpus, simulator, base model) intersect above a declared correlation threshold ρ* (violates evidence independence).
7. **Probabilistic claims requiring a joint distribution:** two certificates carry probabilistic guarantees that would be conjoined but no joint-distribution/multi-objective argument exists (violates T8) — includes any independence assumption between the two.
8. **Non-associative/non-commutative policy combination:** the packs' policies are combined by an order-dependent algorithm (e.g., first-applicable, ordered-*-overrides) and load order is not fixed and certified.
9. **Information-flow / hyperproperty guarantee present:** any pack guarantee is a noninterference/hyperproperty and the composition is not covered by a MAKS-style (T6) side-condition check (default-refute, because these don't compose and refinement doesn't preserve them).
10. **Usage-domain escape:** actual composed usage falls outside any pack's declared usage domain / AoU (violates T9/T10).
11. **Setup/joint-state for cryptographic or protocol guarantees:** a UC-style guarantee is composed without the required trusted setup, or with shared state not handled by JUC (violates T7).

Absent all triggers, packs may compose at L0/L1 (below).

### E. Graded certification ladder (grounded in DO-297 incremental acceptance)

**PROPOSED, mapped to DO-297 tasks:**

- **L0 — Pack-local only.** Each pack/spine validated against its own contract in isolation (analogue: DO-297 Task 1 Module Acceptance §4.2 / Task 2 Application Acceptance §4.3). *Entry:* no trigger fires; disjoint state, acyclic discharged dependencies, disjoint authority, disjoint evidence provenance, declared usage domain. *Evidence:* pack certificate + interface declaration.
- **L1 — Pairwise interaction check.** For each interacting pair, verify the specific channel that connects them (contract discharge, frame disjointness, authority attenuation, evidence-correlation check). *Entry:* triggers 1–3, 5, 6, 8 resolved pairwise. *Evidence:* pairwise interaction certificate; the "composability" property in DO-297 §2.2 (adding a pack does not invalidate an already-integrated pack's verified requirements).
- **L2 — Integration certification over a declared configuration.** Verify the whole configured set within its usage domain: resource allocation, partitioning integrity, joint authority tiers, joint probabilistic/multi-objective claims (analogue: DO-297 Task 3 IMA System Acceptance §4.4 — *no modular credit allowed here*). *Entry:* triggers 4, 7, 9, 10, 11 present, or ≥3 packs share any resource. *Evidence:* integration report; DFA/FFI over shared resources; multi-objective probabilistic argument.
- **L3 — Full joint recertification.** Re-argue end-to-end against the top-level harm hierarchy (analogue: DO-297 Task 4 Aircraft Integration §4.5; ISO 26262 item-level assessment; STAMP/STPA over the whole control structure). *Entry:* safety-relevant cyclic authority, hyperproperty guarantees at system scope, or any change touching Task-3/4-level data (DO-297: such data is explicitly non-reusable). *Evidence:* full assurance case with contract modules binding all pack arguments.

Change management (DO-297 Task 5 Change §4.6): any change re-enters the ladder at the lowest level whose entry criteria the change re-triggers.

### F. Mechanisms that purchase composability by construction

| Mechanism | What it guarantees | Cost | Grounding |
|---|---|---|---|
| Robust time/space partitioning | Disjoint state footprints → frame rule / FFI holds by construction; enables L0/L1 | Hypervisor/scheduler overhead; static resource allocation | ARINC 653; DO-297 (PROVEN precondition + STANDARD) |
| Object-capability attenuation, no ambient authority | Authority bounded by reference graph; policies compose without preplanning; kills confused deputy | Refactor to explicit delegation; credential-broker plumbing | Miller 2006; Hardy 1988 (PROVEN) |
| Append-only, content-addressed fact store (BLAKE3) | Monotonic state → no destructive interference; frame preservation trivial; provenance built-in | Storage growth; no in-place mutation | separation-logic monotonicity (PROVEN); user's existing Δκ/BLAKE3 stack |
| Declared frames + ownership types | Makes trigger #1 statically checkable | Annotation burden | CSL (PROVEN) |
| Non-interference-preserving interfaces (MAKS-checked) | Information-flow guarantees survive composition | Only for BSP-expressible properties; heavy analysis | Mantel 2002 (PROVEN with conditions) |
| Deny-by-default, lattice-ordered policy combination with a proven-associative operator | Order-independent, conflict-free policy composition | Less expressive than XACML's full algorithm set | Bonatti et al. 2002 (PROVEN algebraic) |
| Evidence-provenance tagging | Makes trigger #6 checkable; prevents false confidence multiplication | Metadata discipline on every certificate | Littlewood–Rushby, Assurance 2.0 (EMPIRICAL) |
| Single Authorization Monitor as serialization point | One reference-monitor composition point; serializes authority decisions; provenance-bound | Throughput bottleneck; single choke point | reference-monitor composition; edit/security-automata (Ligatti–Bauer) |

Runtime-enforcement caveat (Ligatti–Bauer–Walker): security automata compose straightforwardly, but *edit* automata (sequence transformers) do not compose trivially, and monitors precisely enforce only safety (under strict transparency) / a limited "infinite renewal" class under relaxed transparency. So a stack of runtime monitors is not automatically a correct monitor for the conjunction.

### G. Invariants and metrics for compositional risk

**PROPOSED (report's own, labeled), with literature grounding where it exists:**

- **Authority-overlap measure** `AO(A,B) = |auth(A) ∩ auth(B)| / |auth(A) ∪ auth(B)|`, plus a boolean **tier-crossing flag** `TC(A,B) = [max_harm_tier(auth(A)∪auth(B)) > max(max_tier(A), max_tier(B))]`. TC is the safety-relevant one (grounded in the lexicographic harm hierarchy + HRU-leakage intuition).
- **Evidence-correlation coefficient** `ρ(A,B)` over shared provenance items (shared verifier/corpus/simulator/base-model = 1 each, weighted). No established metric exists; beta-factor models from common-cause analysis are the closest prior art. Refuse confidence multiplication when ρ > ρ*.
- **Interaction-surface cardinality** `IS = |shared state cells| + |shared tools| + |cross-pack contract edges|`. Heuristic complexity proxy; high IS ⇒ escalate ladder level.
- **Contract-discharge completeness ratio** `CDC = (discharged edges)/(total dependency edges)`. CDC < 1 ⇒ trigger #3. (No literature metric; report's own.)
- **Cycle/well-foundedness flag** from the dependency graph (grounded in A-G soundness conditions).

These extend the user's existing Δκ cross-system-handoff metric to the intra-configuration composition case.

### H. Failure case studies (which channel was the culprit)

1. **Knight Capital (2012)** — STATE-SHARING (+ deployment/config). A repurposed dormant "Power Peg" flag was active on 1 of 8 SMARS routing servers; the system assumed identical logic across servers → divergent shared state. Per SEC Release No. 34-70694 (In the Matter of Knight Capital Americas LLC, Oct 16, 2013): "While processing 212 small retail orders … SMARS routed millions of orders into the market over a 45-minute period, and obtained over 4 million executions in 154 stocks for more than 397 million shares … Ultimately, Knight lost over $460 million from these unwanted positions." First-ever enforcement action under SEC Rule 15c3-5. Independently "validated" components; the interaction (shared flag namespace + no version-consistent state) was uncertified.
2. **Boeing 737 MAX MCAS** — AUTHORITY-OVERLAP. A function granted control authority off a single AoA sensor, able to repeatedly override, without integration-level analysis of its authority interaction with the pilot control loop. A component-interaction accident in the exact STAMP/STPA sense (Leveson: accidents arise from unsafe interactions among components each meeting its own requirements).
3. **Ariane 5 Flight 501 (1996)** — DEPENDENCY + reuse/usage-domain escape. Reused Ariane-4 inertial reference software run outside its validated usage domain (the alignment function remained operative post-liftoff); an unhandled conversion overflow → both IRS units failed identically (common-mode) → loss of guidance 37s after main-engine ignition and vehicle destruction. A reused, "validated" element composed into a new context whose assumptions it violated (ESA/CNES Inquiry Board, 1996).
4. **Cascade problem (TCSEC Red Book / Trusted Network Interpretation)** — EVIDENCE/PROPERTY across accreditation boundaries. Individually accredited systems compose into an end-to-end path whose aggregate risk exceeds any component's accredited range; detected via the nesting condition / cascade condition. The archetypal "independently certified ⇒ jointly unsafe" result.
5. **Telecom feature interaction** — DEPENDENCY/STATE. Independently correct features (call-forwarding, call-waiting, etc.) produce contradictory behavior when composed; the canonical demonstration that independently validated features break on composition, with consensus that no universal generic resolution exists.
6. **LLM-agent confused deputy at a shared tool surface** — AUTHORITY-OVERLAP (contemporary). Multiple packs/agents sharing a tool credential; injected content redirects the deputy's authority; multi-agent delegation propagates it across trust boundaries without per-call, provenance-bound authorization (Cloud Security Alliance 2026; cross-framework audits find "capability gating shipped, per-call authorization absent").

### I. Open problems / what remains unsolved

- **Learned/stochastic components.** No accepted way to write sound contracts for LLM-based packs whose specifications are informal; probabilistic guarantees compose only via multi-objective machinery (Kwiatkowska) that presumes formal models. Assumption generation for learning-enabled systems (Pasareanu et al. 2023) is nascent.
- **Evidence composition has no theorem.** Correlation accounting is the state of the art; conservative Bayesian inference gives bounds, not composition.
- **Hyperproperty composition** remains hard; refinement does not preserve security (refinement paradox), so top-down refinement of a composed argument can silently break information-flow guarantees.
- **Authority-leakage decidability wall.** HRU undecidability means any general "does authority overlap grant an unintended permission?" checker is impossible; only restricted models (monotone/mono-operational, object-capability) are tractable.
- **LLM-agent guardrail composition** is empirically fragile and heuristic; layering is a posture, not a proof, and layers can interfere (false-positive compounding) as well as fail to cover indirect injection.
- **AI-control protocol composition.** Whether control evaluations (Greenblatt et al. 2023; Korbak et al. 2025 AI Control Levels ACL-1..5) compose across protocol components is not established; the "perfect strategist" assumption and shared-context effects complicate additive safety claims.

### J. Practitioner's checklist + YAML schema

**Checklist (paste-ready):**
1. Declare each pack's interface: imports, exports, shared-state cells, authority set (with harm tiers), evidence provenance, usage domain.
2. Build the dependency graph; assert acyclic OR attach a well-founded discharge.
3. Verify every dependency edge's contract discharge (CDC = 1).
4. Check frame disjointness of all shared mutable state.
5. Compute AO and TC for every pack pair; escalate on tier-crossing.
6. Require per-invocation, provenance-bound authorization on every shared tool.
7. Compute evidence-correlation ρ; do not multiply confidences above ρ*.
8. Confirm the policy combination operator is associative/commutative or fix + certify load order.
9. Default-refute any hyperproperty/noninterference guarantee unless MAKS-checked.
10. Run the §D trigger predicate; assign ladder level L0–L3; record required evidence per level.
11. On any change, re-enter the ladder at the lowest re-triggered level.

**YAML pack-interaction schema (PROPOSED):**
```yaml
pack:
  id: "domain-pack-medical-v2"
  version: "2.1.0"
  spine_compat: ">=1.8"
  imports:                      # dependency edges (this pack assumes)
    - from: "core.authz_monitor"
      assumes: "A_authz"        # contract assumption id
  exports:
    - guarantee: "G_phi_redaction"
      type: "safety"            # safety | liveness | hyperproperty | probabilistic
      prob: null                # e.g. 0.999 if probabilistic; forces multi-objective join
  shared_state:
    - cell: "core.fact_store"
      access: "append_only"     # append_only | read | read_write
      frame_declared: true
  authority:
    set: ["tool.db.read", "tool.email.send"]
    harm_tiers: {tool.db.read: 1, tool.email.send: 2}
    attenuated: true            # object-capability membrane in place
    ambient: false
  evidence_provenance:
    verifier: "verifier-X@3.2"
    corpus: "blake3:9f2c..."    # content-addressed
    simulator: "sim-Y@1.4"
    base_model: "model-Z@2026-05"
  usage_domain:
    conditions: ["input_lang=en", "max_tools=8"]
  policy:
    combinator: "deny-overrides"  # must be associative/commutative
    load_order_fixed: true
  dependency_discharge:
    cycles: false
    well_founded_proof: null      # required iff cycles: true
```
A registry linter runs the §D trigger predicate over the union of these declarations and emits the required ladder level (L0–L3) and the missing evidence per pack pair.

## Recommendations

1. **Adopt the trigger predicate (§D) as a hard registry lint gate now.** Any pack pair that fires a trigger cannot ship at L0. This is the single highest-leverage control: it turns "compositional sufficiency" into a checkable property over declared interfaces. Threshold to change: if the false-positive rate on triggers 4/6/9 blocks routine composition, tune ρ* and the harm-tier map, not the predicate structure.
2. **Buy composability by construction (§F) so most pairs stay at L0/L1.** Mandate robust partitioning for state, object-capability attenuation for authority, an append-only content-addressed fact store for shared state, and route all authority decisions through the single Authorization Monitor. These convert three of the four channels from "must analyze" to "safe by construction."
3. **Treat evidence provenance as first-class certificate metadata.** Require verifier/corpus/simulator/base-model tags on every pack certificate and refuse to multiply confidences whose provenance overlaps (trigger #6). This is the only defense against the Knight–Leveson / Littlewood–Rushby non-independence result, which no amount of property-level rigor fixes.
4. **Default-refute hyperproperty and probabilistic composition.** Never conjoin information-flow or probabilistic guarantees without, respectively, a MAKS-style side-condition check or an explicit multi-objective/joint-distribution argument. Benchmark: if a pack exports a hyperproperty guarantee, it enters L2 automatically.
5. **Ground the ladder in DO-297 discipline.** Grant modular credit only at L0/L1 (Task 1/2 analogue); forbid it at L2/L3 (Task 3/4 analogue). Require a declared usage domain per pack and verify actual composed usage stays inside it — usage-domain escape is trigger #10.
6. **Staged rollout:** (a) implement the YAML schema + linter for triggers 1–3, 5, 6, 8 (statically checkable) first; (b) add authority-tier (4) and usage-domain (10) checks once the harm hierarchy is encoded; (c) add hyperproperty/probabilistic gating (7, 9, 11) last, since these require the most analyst input.

## Caveats

- **Distinguish PROVEN / STANDARDIZED / EMPIRICAL / PROPOSED throughout.** Theorems T1–T8 are PROVEN with stated preconditions; T9–T10 are STANDARDIZED practice (not theorems); the evidence-independence results are EMPIRICAL (strongly replicated); the trigger predicate, ladder, metrics, and YAML schema are the report's own PROPOSED synthesis and have not been validated in the literature.
- **DO-297 task numbering is authoritative but the standard text is paywalled.** Task names/subsection mapping come from FAA AC 20-170's explicit mapping (Task 1=§4.2 Module, 2=§4.3 Application, 3=§4.4 IMA System, 4=§4.5 Aircraft Integration, 5=§4.6 Change, 6=§4.7 Reuse); "continued airworthiness" is DO-297 Chapter 6, NOT a Section-4 task. Verbatim in-standard section titles were not directly readable.
- **Undecidability limits automation.** Trigger #4 (authority leakage) cannot be decided in general (HRU); the registry linter must use the conservative tier-crossing over-approximation, which will over-trigger.
- **The metrics in §G are largely novel.** Only the beta-factor/common-cause grounding for ρ and the A-G soundness grounding for the cycle flag rest on established work; AO, IS, and CDC are defensible constructions, not literature-standard measures.
- **LLM-agent composition evidence is recent and partly from vendor/practitioner sources.** The confused-deputy and guardrail-layering claims draw on 2026 practitioner and CSA material plus the Greenblatt/Korbak AI-control line; these are less settled than the formal-methods and certification-standard citations.
- **Some source dates reflect the current corpus (2025–2026 papers).** Where a 2026 replication (N-version with coding agents, arXiv:2606.20158) or 2026 practitioner note is cited, it corroborates rather than establishes the underlying classical result.