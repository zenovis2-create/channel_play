# Truth Pen License Review

Task: `task-0009`

Reviewer: `critic_reviewer`

Reviewed: 2026-07-26

Verdict: **CHANGES REQUIRED**

Risk: **HIGH**

Asset factory gate: **BLOCKED**

## Findings

1. **BLOCKER — Required research evidence is missing.** The task requires a
   successful NotebookLM/Maru cited brief
   (`memory/company/task-0009-plan.md:7`), but both recorded research adapter
   runs failed. Official-source research is useful but is not the named evidence
   unless `chief_orchestrator` explicitly approves that substitution.
2. **HIGH — No project ownership chain exists yet.** The proposed creator is
   only “Channel Play project team,” while the contributor agreement or rights
   assignment remains unrecorded
   (`docs/research/truth_pen_source_license_brief.md:27`). Do not label an asset
   project-owned until the creator, contracting parties, jurisdiction, and
   commercial/modification/redistribution/marketing rights are documented.
3. **HIGH — The production gate is circular.** The brief requires job IDs and
   output hashes before `asset_factory` begins, although those records cannot
   exist before generation (`docs/research/truth_pen_source_license_brief.md:59`
   and `:73`). Split the gate into pre-generation authorization and pre-import
   acceptance.
4. **HIGH — OpenAI rights language is too broad.** “Owned Output” is a
   contractual allocation between the applicable parties and only to the extent
   permitted by law; it is not a guarantee of copyrightability, exclusivity, or
   non-infringement. Record the legal account holder, individual/API/Business
   product, model/tool, beta status, and any third-party service before use.
5. **MEDIUM — Provider restrictions need a separate matrix.** The cited 2022
   sharing policy specifically discusses social sharing, demonstrations, and
   API-assisted written works. Do not automatically extend its disclosure rule
   to every in-game image. Determine the policies applicable to the actual
   generation path.

The OpenAI findings are consistent with the current
[Terms of Use](https://openai.com/policies/terms-of-use/),
[Services Agreement](https://openai.com/policies/services-agreement/),
[Service Terms](https://openai.com/policies/service-terms/), and
[Sharing & Publication Policy](https://openai.com/policies/sharing-publication-policy/).
The CC0 summary is acceptable, subject to work-specific provenance and the
trademark, patent, privacy, publicity, endorsement, and warranty limitations in
the [CC0 Deed](https://creativecommons.org/publicdomain/zero/1.0/) and
[Legal Code](https://creativecommons.org/publicdomain/zero/1.0/legalcode.en).

## Required Gates

### Gate A — Generation Authorization

- Select one path: commissioned human work, OpenAI generation, or a specific
  CC0 work.
- Record the human rights agreement, AI account and applicable terms, or exact
  CC0 work URL and authorized affirmer.
- Confirm all input rights and prohibit unverified web references, tracing, and
  image conditioning.
- Attach the required research evidence or an explicit orchestrator-approved
  substitute, followed by a new critic approval.

### Gate B — Download, 3D Production, and Unity Import

- Record timestamp, prompt, job/seed, original and accepted SHA-256 hashes, and
  modification history.
- Pass dated reverse-image, logo, watermark, trademark, character, likeness,
  privacy, and publicity checks.
- Resolve attribution and AI disclosure for the selected path.
- Mark commercial use, derivatives, and redistribution as `PASS` with no
  unknown fields.

Any missing or unknown field keeps the gate closed. This review is a production
risk assessment, not legal advice.
