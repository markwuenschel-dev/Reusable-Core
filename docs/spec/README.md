# Reusable Core specification, v1.10

This folder contains the whole specification. Start with the kernel.

| Read | When |
|---|---|
| **[Kernel — `reusable-core-v1.10-kernel.md`](reusable-core-v1.10-kernel.md)** | Always first. It is the normative spec, and every section states what is built in this repository today. §0.4 is the one-screen dashboard; §20.3 says what to build next. |
| [Vol. I — Core architecture detail](volumes/vol-1-core-architecture.md) | Full mechanics behind a kernel section: the loop, broker, verification stack, risk math, contracts, memory, federation, telemetry, domain-pack schema. |
| [Vol. II — Canonical implementation profile](volumes/vol-2-implementation-profile.md) | Choosing real technology: identity, Cedar/OPA, PostgreSQL authority state, sandboxes, model fabric, certification durability, composition, interfaces, the acceptance suite. |
| [Vol. III — Trusted runtime + Model Factory](volumes/vol-3-trusted-runtime-and-model-factory.md) | Runtime trust model and the governed learning loop: router, specialist, and verifier factories; epistemic stability. |
| [Vol. IV — Research program](volumes/vol-4-research-program.md) | Running an experiment: RQ1–RQ26 priors, treatment ladders, injection batteries, the E1 field record, open tensions. **Non-normative.** |
| [`sources/`](sources/) | The original research reports behind Vol. II. **Non-normative.** |

## Precedence

```text
kernel  >  Vol. I  >  Vol. II  >  Vol. III          normative
Vol. IV, sources                                    non-normative, grant no authority
```

If a volume and the kernel disagree, the kernel wins and the volume has a defect. The volumes are reproduced byte-for-byte from their last revision below a short header, so their internal text still says "v1.9" and uses the former document names (CORE, ROUTING, RUNTIME, FACTORY, COMPOSITION, CERTDUR).

## Keeping status honest

Each kernel section ends with an **Implementation status** block (BUILT / PARTIAL / NOT STARTED / NEXT), measured against a named commit. Kernel §20.1.6 requires a PR that changes a section's status to update that block and the §0.4 dashboard. When the status changes, also update the commit reference at the top of the kernel.

## Supersession map

v1.10 restructures twenty source files into one kernel, four volumes, and four source reports. Paragraph-level comparison confirmed that each family's latest revision contains every paragraph of its earlier revisions except intentionally revised ones (version headers, precedence lists, and the factory roadmap Gantt chart and milestone table, which were rewritten in later revisions). Nothing else was dropped.

| Former file | SHA-256 (prefix) | Disposition |
|---|---|---|
| `Reusable_Core_Domain-Agnostic_Agent_Loop_v1_9.md` | `94b985a8fb3f` | **→ Vol. I**; summarized normatively in the kernel |
| `Reusable_Core_Canonical_Implementation_Architecture_2026_RQ17_RQ18_RQ26_integrated_math_latex_fixed.md` | `0e80d9a33353` | **→ Vol. II** (implementation profile 1.2) |
| `…Canonical_Implementation_Architecture_2026_RQ17_RQ18_RQ26_integrated_math.md` | `e5cf407e16de` | superseded by the LaTeX-fixed revision |
| `…Canonical_Implementation_Architecture_2026_RQ18_RQ26_integrated_math.md` | `a76f0a3ef62c` | superseded (profile 1.1) |
| `…Canonical_Implementation_Architecture_2026_RQ26_integrated_math_fixed.md` | `f61e116993db` | superseded |
| `Reusable_Core_Canonical_Implementation_Architecture_2026.md` | `3a8fd0297d22` | superseded (profile 1.0) |
| `Trusted_Runtime_and_Self-Improving_Model_Portfolio_for_Reusable_Core_v1_9_RQ17_RQ18_RQ26_integrated_math_latex_fixed.md` | `224113857693` | **→ Vol. III** |
| `…Model_Portfolio_for_Reusable_Core_v1_9_RQ17_RQ18_RQ26_integrated_math.md` | `e4db14f4499e` | superseded by the LaTeX-fixed revision |
| `…Model_Portfolio_for_Reusable_Core_v1_9_RQ18_RQ26_integrated_math.md` | `07429bf0d48a` | superseded |
| `…Model_Portfolio_for_Reusable_Core_v1_9_RQ26_integrated_math_fixed.md` | `d31df07311ae` | superseded |
| `Trusted_Runtime_and_Self-Improving_Model_Portfolio_for_Reusable_Core_v1.9.md` | `ec4e77db6c22` | superseded (original) |
| `Reusable_Core_Research_Program_v1_9_RQ17_RQ18_RQ26_integrated_math_latex_fixed.md` | `a4c70a045a53` | **→ Vol. IV** |
| `…Research_Program_v1_9_RQ17_RQ18_RQ26_integrated_math.md` | `4e85a05fd594` | superseded by the LaTeX-fixed revision |
| `…Research_Program_v1_9_RQ18_RQ26_integrated_math.md` | `fc0bd2642723` | superseded |
| `…Research_Program_v1_9_RQ26_integrated_math_fixed.md` | `0b0cee1d4cbf` | superseded |
| `Reusable_Core_Research_Program_v1_9.md` | `dd6f7ae4680f` | superseded (original) |
| `Building_a_Nemotron-Style_System_of_Routed_AI_Agents.md` | `aa36694c871d` | **→ `sources/routed-agents-nemotron.md`** |
| `Trusted_Runtime_Architecture_for_the_Reusable_Core_in_2026.md` | `56ba27db1905` | **→ `sources/trusted-runtime-architecture-2026.md`** |
| `Compositional_Sufficiency_Across_Spines_and_Domain_Packs.md` | `8a3f5e87f35c` | **→ `sources/rq17-compositional-sufficiency.md`** |
| `RQ18___Certification_Durability_Under_Drift_and_Change.md` | `389207522250` | **→ `sources/rq18-certification-durability.md`** |

Superseded revisions are not committed here; the hashes above identify them if anyone needs to recover one.
