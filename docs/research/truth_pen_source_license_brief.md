# Truth Pen Source and License Brief

Task: `task-0009`

Prepared: 2026-07-26

Revised: 2026-07-26 after critic review

Status: research approved and closed fail-closed; production source not approved

## Executive Decision

**No safe production source has been found or approved.** No image, model,
concept sheet, or generated output was acquired. The existing
`asset_pipeline/briefs/truth_pen.md` is a design requirement, not source art and
not proof that Channel Play owns any future asset.

`asset_factory` remains blocked. A future commissioned-human, OpenAI, or
work-specific CC0 path may pass Gate A below, but none currently does. Generic
web or social images remain rejected.

## Evidence Decision

For this task, `chief_orchestrator` approved official controlling terms plus
dated retrieval records and critic receipts as the research evidence. This
task-scoped substitution is recorded in
`memory/company/task-0009-evidence-decision.md`. Failed NotebookLM and `agy`
receipts remain part of the audit trail and are not represented as successful.

## Candidate Source Status

| Path | Provider/source | Creator or affirmer | License/rights basis | Status |
| --- | --- | --- | --- | --- |
| New commissioned human work | Not selected | Unknown | Signed project agreement or written assignment required | **Not approved** |
| OpenAI-generated original | Product/account not selected; no generation performed | Account holder and producing contributor unknown | Applicable OpenAI agreement plus any contributor-to-project assignment | **Not approved** |
| External CC0 work | No work-specific URL selected | Unknown | Exact work must be validly associated with CC0 by an authorized affirmer | **Not approved** |
| Generic search/social image | Unverified web source | Unknown | Unknown | **Rejected** |

The final record must identify the actual natural-person creator or authorized
affirmer, contracting parties, applicable jurisdiction, and rights covering
commercial use, modification, redistribution, and marketing. Repository or Git
authorship alone is not a rights assignment.

## Official Controlling Sources

Sources were retrieved on 2026-07-26.

| Source | Controlling point for this decision |
| --- | --- |
| [OpenAI Terms of Use](https://openai.com/policies/terms-of-use/) (effective 2026-01-01) | Applies to individual services. Output ownership language is only between the user and OpenAI and to the extent permitted by law. Input rights, non-uniqueness, human review, and third-party rights remain user responsibilities. |
| [OpenAI Services Agreement](https://openai.com/policies/services-agreement/) (effective 2026-01-01) | Applies to APIs and business services. Output allocation is between Customer and OpenAI; Customer must hold Input rights and is responsible for Output use and suitability. |
| [OpenAI Service Terms](https://openai.com/policies/service-terms/) (updated 2026-06-12) | API/Enterprise indemnity has material exceptions. Visual likeness needs consent and rights. Public sharing on the Services grants additional platform licenses. Third-party App content in Output is not owned by the user or OpenAI. Beta services have reduced protections. |
| [OpenAI Usage Policies](https://openai.com/policies/usage-policies/) (effective 2025-10-29) | Prohibits attempts to infringe others' IP and confusing use of a person's likeness without consent. It does not replace legal clearance. |
| [OpenAI Sharing & Publication Policy](https://openai.com/policies/sharing-publication-policy/) (updated 2022-11-14) | Specifically addresses social sharing, livestreams, demonstrations, and API-assisted written works. It is not treated here as a blanket disclosure rule for every game image. |
| [CC0 1.0 Deed](https://creativecommons.org/publicdomain/zero/1.0/) and [Legal Code](https://creativecommons.org/publicdomain/zero/1.0/legalcode.en) | A valid CC0 dedication permits commercial copying, modification, and redistribution without attribution as a copyright condition. It supplies no warranty and does not clear patent, trademark, privacy, publicity, or endorsement issues. The legal code controls. |

## Rights Matrix

| Path | Commercial use | Derivatives | Redistribution | Attribution/disclosure | Generative-provider restrictions |
| --- | --- | --- | --- | --- | --- |
| Commissioned human | `UNKNOWN` until signed rights instrument | `UNKNOWN` | `UNKNOWN` | Contract/project policy | Not applicable unless AI is used |
| OpenAI-generated | `UNKNOWN` until product, account, Input, and applicable terms are recorded | Contractual Output allocation may permit use, but does not guarantee copyrightability or exclusivity | `UNKNOWN` until the same review | Never misrepresent AI Output as human-generated; determine asset-facing disclosure for the actual publishing context | See separate matrix below |
| Work-specific CC0 | `PASS` only after authority and exact-work verification | Same | Same | No CC0 attribution condition; retain internal provenance and avoid implied endorsement | Not applicable |
| Generic web image | `FAIL` | `FAIL` | `FAIL` | Unknown | Unknown |

## OpenAI Path Restrictions

An OpenAI path cannot pass based only on the provider name.

| Field | Gate A requirement |
| --- | --- |
| Legal customer | Name the individual or organization that accepted the terms and can transfer relevant rights to Channel Play |
| Product and account | Record individual ChatGPT or API/Business/Enterprise, workspace owner, intended model/tool, and beta status |
| Input rights | Use only cleared project text; no unverified image reference, tracing, or image conditioning |
| Contractual Output allocation | Record the applicable agreement and state that it is not a copyrightability, exclusivity, title, or non-infringement warranty |
| Similarity and human review | Accept non-uniqueness; perform design, trademark, character, and likeness review |
| Visual capabilities | Do not reproduce a person's likeness without express consent and necessary rights |
| Public-on-service sharing | If used, record the additional OpenAI/user platform licenses; otherwise do not publish the source through a public feed |
| Third-party Apps/GPTs | Prohibited unless their separate terms and Output rights are reviewed; third-party App content is outside OpenAI/user ownership allocation |
| Indemnity and beta limits | Do not treat indemnity as clearance; record exceptions for modified/combined Output, trademarks, unlicensed Input, ignored safeguards, Third Party Offerings, and Beta Services |
| AI disclosure | Maintain internal AI provenance. Determine external disclosure from the actual product, publishing context, current terms, and project policy |

## Gate A — Generation Authorization

All applicable fields must be `PASS` before creating or downloading source art.

- Select exactly one path and identify its provider, source, creator/affirmer,
  license or agreement, retrieval date, and controlling terms.
- Human path: attach the signed agreement or assignment covering commercial use,
  modification, redistribution, marketing, and downstream asset creation.
- OpenAI path: complete every field in the provider matrix and confirm the
  producing contributor can transfer relevant rights to the project.
- CC0 path: record the exact work URL, creator/affirmer, original host, CC0
  marking, retrieval snapshot, and evidence that the affirmer was authorized.
- Confirm all Input rights and prohibit unknown web references, watermarks,
  logos, copied franchise styling, tracing, and image conditioning.
- Attach this research evidence and a fresh `critic_reviewer` approval.

Current Gate A result: **FAIL — no path or rights chain selected.**

## Gate B — Production and Unity Import

Gate B occurs only after Gate A passes and an output exists.

- Record generation/acquisition timestamp, prompt, model/tool, job/seed when
  available, and original/accepted SHA-256 hashes.
- Record every edit, editor, derivative tool, file conversion, and review date.
- Pass dated reverse-image-similarity, logo, watermark, trademark, recognizable
  character, likeness, privacy, publicity, and endorsement checks.
- Resolve required credit and AI disclosure text for the selected path.
- Mark commercial use, derivatives, and redistribution `PASS`; no field may be
  unknown.
- Attach final provenance and reviewer sign-off before 3D production or Unity
  import.

Current Gate B result: **NOT STARTED — Gate A failed and no output exists.**

## Handoff

This research task may close with the fail-closed result above, but it does not
authorize asset production. `asset_factory` must wait for a separately completed
Gate A record and fresh critic approval. Counsel should review prominent
branding, merchandising, or high-value commercial release. This document is a
production risk assessment, not legal advice.
