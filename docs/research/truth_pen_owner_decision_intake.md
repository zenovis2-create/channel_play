# Truth Pen Owner Decision Intake

Task: `task-0014`

Status: owner decisions incomplete; all artist contact remains blocked

## Purpose

Use the repository-safe decision record to authorize a written, proposal-only
contact. It does not authorize artist selection, contracting, artwork, source
files, payment, or Gate A approval.

```powershell
python tools/channelctl asset procurement-init truth_pen
python tools/channelctl asset procurement-check truth_pen
```

Edit `asset_pipeline/manifests/truth_pen_procurement_decision.json`. The
initial template is intentionally incomplete and the check must return `FAIL`.
Initialization records the normalized SHA-256 of the current RFP and
procurement packet. Do not replace either hash unless the owner has reviewed
the changed document and is renewing authorization.

## Repository-Safe Owner Decisions

Complete these fields only after the owner makes the corresponding decision:

- `owner.secure_record_id`: secure-system identifier in the exact form
  `vault:<canonical-lowercase-UUID>`; never a person's name, email, tax number,
  account number, or card number;
- `owner.authorized_signer_role`: `project_owner`,
  `authorized_company_officer`, or `producer`;
- `owner.governing_jurisdiction`: short code such as `KR` or `US-CA`;
- positive budget ceiling, three-letter currency, and payment route
  (`upwork`, `fiverr`, or `direct`);
- secure tax/vendor-process confirmation, proposal deadline, delivery date,
  and revision limit;
- `outreach.scope`: `one` with one candidate ID, or `all` with all three;
- explicit authorization and its timezone-aware ISO-8601 timestamp; and
- confirmation that sensitive records remain outside the repository.

Candidate IDs are `cynthia_ignacio`, `marisol_griffiths`, and
`natalie_lewis`. Use only the IDs the owner explicitly authorizes.

## Never Commit

Do not put personal names, identity documents, tax identifiers, banking
details, payment credentials, signatures, private addresses, or private
messages in this manifest. Store them in the owner's approved secure system
and record only its opaque identifier.

The checker rejects unexpected fields and any privacy flag indicating sensitive
data is present. It also rejects non-standard JSON values such as `NaN` and
`Infinity`. This is a structural safeguard, not a substitute for a manual
privacy review.

## Authorization Boundary

A `PASS` authorizes sending only the existing written RFP and proposal request
whose normalized SHA-256 values are bound in the decision record, and only to
the recorded candidate IDs. Any RFP or packet edit invalidates authorization
until the owner reviews the change and binds the new hash. Do not ask for
sketches, art tests, source files, or generated images. Source creation remains
blocked until the selected artist signs the final agreement and Gate A passes.

Current receipt:
`runs/asset-procurement-truth_pen/outreach_readiness_check.md`.
