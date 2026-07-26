# Truth Pen Gate A Commissioning Packet

Task: `task-0011`

Decision date: 2026-07-26

Decision owner: project orchestration

Status: `commissioned_human` selected; source creation remains blocked

Procurement follow-up:
`docs/research/truth_pen_artist_procurement_packet.md` and
`asset_pipeline/briefs/truth_pen_commission_rfp.md`

## Decision

Use a newly commissioned human work as the Truth Pen source strategy. This
choice creates the clearest project-specific chain from a named creator to
Channel Play and avoids depending on an unidentified account, generated output,
or third-party CC0 work. It is a procurement decision only: no artist, contract,
source artwork, or rights approval is represented as existing.

The canonical manifest now selects `commissioned_human`, but Gate A remains
`FAIL`. Do not request sketches, accept source files, generate images, or begin
3D work until every item below is evidenced and the gate passes.

## Owner Intake

The project owner must provide verified, non-placeholder answers:

- legal name of each contracting party and the applicable jurisdiction;
- natural-person creator(s), employer or studio if any, and the party able to
  grant rights to Channel Play;
- signed agreement or assignment covering commercial use, modification,
  redistribution, marketing, and downstream 3D/Unity asset creation;
- declaration of all inputs, references, subcontractors, and any generative-AI
  use, with proof that each input is project-owned or cleared;
- confirmation that the work excludes unverified web references, watermarks,
  logos, copied franchise styling, tracing, image conditioning, and unlicensed
  likenesses; and
- retrieval/execution date plus the exact agreement and source references.

Do not commit private contact, payment, tax, government-ID, or bank information.
Store a reviewable, redacted rights copy in the repository and retain the
unredacted original in the project's controlled contract system.

## Evidence-to-Manifest Map

| Manifest field | Required evidence |
| --- | --- |
| `schema` | Keep `channel_play.asset_source_gate_a.v1` |
| `asset_id` | Keep the canonical `truth_pen` ID |
| `task_id` | Keep the authorized sourcing task, `task-0011` |
| `source_path` | Keep the selected `commissioned_human` strategy |
| `applicable_jurisdiction` | Contract review or project-owner confirmation |
| `provider_or_source` / `creator_or_affirmer` | Named studio and actual creator declaration |
| `rights_holder_or_legal_customer` | Party granting or receiving the project rights |
| `license_or_agreement` | Agreement title, version, and execution date |
| `source_reference` | Repository record describing the commissioned work |
| `retrieval_date` | Agreement/evidence review date in `YYYY-MM-DD`, never a future date |
| `controlling_terms_reference` | Redacted signed instrument or counsel-approved summary |
| `rights.*` | Explicit reviewer finding for all four `PASS` values |
| `input_clearance.*` | Signed creator declaration and project input inventory |
| `path_details.contracting_parties` | Exact parties shown by the rights instrument |
| `path_details.signed_rights_instrument` | Repository-relative evidence path |
| `path_details.downstream_asset_creation_grant` | Explicitly supported `true` finding |
| `evidence_paths` | All supporting repository-relative records |
| `critic_review.receipt` | Repository-relative path to the structured JSON approval |

Suggested evidence destinations, created only when genuine evidence exists:

```text
docs/research/truth_pen_gate_a_evidence/rights_summary.md
docs/research/truth_pen_gate_a_evidence/creator_declaration.md
docs/research/truth_pen_gate_a_evidence/input_inventory.md
docs/research/truth_pen_gate_a_evidence/signed_instrument_redacted.pdf
```

## Approval Sequence

1. Collect and review the genuine documents above; use counsel where the rights
   chain, jurisdiction, branding, likeness, or commercial exposure warrants it.
2. Fill `asset_pipeline/manifests/truth_pen_source_gate_a.json` from those
   documents. Never use placeholder names, dates, URLs, or `PASS` values.
3. Set the intended structured critic receipt path, then run:

   ```powershell
   python tools/channelctl asset gate-a-check truth_pen
   ```

4. Ask `critic_reviewer` to review the exact manifest and bind approval to its
   current SHA-256. The receipt must be a JSON object with these exact values:

   - `schema`: `channel_play.critic_gate_approval.v1`
   - `asset_id`: `truth_pen`
   - `task_id`: the exact `task_id` in the manifest
   - `gate`: `A`
   - `manifest_sha256`: SHA-256 shown by `asset gate-a-check`; gate-record
     CRLF/CR line endings are normalized to LF before hashing
   - `reviewer_role`: `critic_reviewer`
   - `verdict`: `APPROVED`
   - `source_creation_authorized`: `true`
   - `production_authorized`: `false`
   - `reviewed_at`: non-future ISO-8601 timestamp with timezone, dated no
     earlier than the manifest's `retrieval_date`

   Set the receipt path in the manifest before hashing it. The receipt itself
   is a separate repository file, so this does not create a circular hash. Any
   later manifest edit invalidates the approval.
5. Run the check again. Source creation is allowed only when the receipt says
   `Result: **PASS**`.

Gate A does not authorize 3D production or Unity import. After an approved
source is created, complete Gate B separately. This packet is a production risk
control, not legal advice or a rights instrument.
