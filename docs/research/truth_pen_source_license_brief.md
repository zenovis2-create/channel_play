# Truth Pen Source and License Brief

Task: `task-0009`

Prepared: 2026-07-26

Status: ready for critic review; no source art approved or acquired

## Decision

Use an original Channel Play concept derived only from
`asset_pipeline/briefs/truth_pen.md`. The preferred production path is a new
human-authored design made under the project's contributor/IP agreement. An
OpenAI-generated concept from the same project-owned brief is an acceptable
conditional alternative after the account type and applicable terms are
recorded. Do not use a found web image as a source.

This decision approves a **source strategy**, not an asset. Generation, download,
and import remain blocked until `critic_reviewer` accepts this brief and the
production record below is complete.

## Project-Owned Concept Record

| Field | Record |
| --- | --- |
| Provider/source | Channel Play repository, `asset_pipeline/briefs/truth_pen.md` |
| Creator | Channel Play project team; the producing contributor must be named in the final record |
| Rights basis | New work created for the project; confirm the contributor agreement or written assignment |
| Required form | Chunky gold-and-charcoal pen, cyan emissive nib, asymmetric clip; no text, logos, watermark, hands, or copied franchise styling |
| Intended use | Commercial game prop, shop icon, world pickup, marketing capture, and modified derivatives |

Because the repository does not contain a contributor agreement, the final art
record must not claim project ownership until that agreement or assignment is
identified.

## Controlling Sources

Sources were retrieved on 2026-07-26.

| Source | Controlling point |
| --- | --- |
| [OpenAI Terms of Use](https://openai.com/policies/terms-of-use/) (effective 2026-01-01) | For individual services, the user retains Input rights and owns Output as between the user and OpenAI, to the extent permitted by law. Input rights, human review, non-uniqueness, and third-party rights remain the user's responsibility. |
| [OpenAI Services Agreement](https://openai.com/policies/services-agreement/) (effective 2026-01-01) | For APIs and business services, the customer owns Output as between the parties, but must hold Input rights and evaluate the Output's fitness and accuracy. |
| [OpenAI Service Terms](https://openai.com/policies/service-terms/) (updated 2026-06-12) | API IP indemnity has exceptions, including unlicensed Input, ignored safeguards, modified/combined Output, trademark use in commerce, and Third Party Offerings. It is risk allocation, not source clearance. |
| [OpenAI Sharing & Publication Policy](https://openai.com/policies/sharing-publication-policy/) (updated 2022-11-14) | Shared generations require manual review, attribution to the person/company, and clear AI disclosure. |
| [CC0 1.0 Deed](https://creativecommons.org/publicdomain/zero/1.0/) and [Legal Code](https://creativecommons.org/publicdomain/zero/1.0/legalcode.en) | CC0 permits copying, modification, distribution, and commercial use without permission. It does not clear patent, trademark, publicity, or privacy rights and supplies no warranty. The legal code controls. |

## Rights Matrix

| Strategy | Commercial use | Derivatives | Redistribution | Attribution | Restrictions and residual risk |
| --- | --- | --- | --- | --- | --- |
| New human-authored project work — **preferred** | Yes, after contributor rights are documented | Yes | Yes | Internal creator credit per project policy | Avoid third-party references; retain drafts and assignment |
| OpenAI-generated original — **conditional** | Not prohibited under the applicable terms, subject to compliance | Allowed as owned Output; modification can narrow API indemnity | Allowed subject to terms | Record AI use; publication policy calls for company/person attribution and AI disclosure | Output may be similar or infringing; no non-infringement warranty; screen trademarks and recognizable designs |
| Verified CC0 work — fallback only | Yes | Yes | Yes | Not legally required by CC0; record source anyway | Verify the uploader controlled the work; separately clear trademark, privacy, publicity, and endorsement concerns |
| Generic search/social image | **Rejected** | Unknown | Unknown | Unknown | Unknown provenance, watermark, platform terms, or branding fails the gate |

## Production Provenance Record

Before `asset_factory` begins, record:

- final creator/provider, source URL or internal file, and retrieval/generation
  timestamp;
- applicable account type, model/tool version, prompt, seed or job ID when
  available, and a snapshot/link to the terms in force;
- original and accepted-file SHA-256 hashes, edits, editor, and review date;
- contributor agreement/assignment reference or exact external license;
- trademark/logo, watermark, recognizable-character, privacy/publicity, and
  reverse-image-similarity checks;
- required credit and AI disclosure text.

## Handoff and Open Risks

`asset_factory` should receive the approved brief plus the completed provenance
record, then create the concept from scratch. It must not trace or image-condition
on unverified web material. The reviewer should fail closed if creator rights,
applicable provider terms, or screening evidence are missing.

This is a production risk assessment, not legal advice. Counsel should review
material intended for prominent branding, merchandising, or high-value
commercial release.
