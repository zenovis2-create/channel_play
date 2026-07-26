# Asset Procurement Outreach Readiness

Asset ID: truth_pen
Checked: 2026-07-26T23:16:01+09:00
Decision: asset_pipeline/manifests/truth_pen_procurement_decision.json
Decision SHA-256: ebd90c2d28c3bc2e7b763b323ba5da71a3067fcd51a8612facfff451bdff9a2f
Result: **FAIL**

## Findings

- decision_status must be approved_for_proposal_outreach
- owner.secure_record_id must use vault:<canonical-lowercase-UUID>
- owner.authorized_signer_role must be project_owner, authorized_company_officer, or producer
- owner.governing_jurisdiction must use a repository-safe code such as KR or US-CA
- commercial.budget_ceiling must be a positive finite number
- commercial.currency must be a three-letter currency code
- commercial.payment_route must be upwork, fiverr, or direct
- commercial.tax_vendor_process_confirmed_securely must be true
- schedule.proposal_deadline must use YYYY-MM-DD
- schedule.desired_delivery_date must use YYYY-MM-DD
- schedule.revision_limit must be an integer from 1 to 10
- outreach.authorized must be true
- outreach.authorized_at must be an ISO-8601 timestamp
- outreach.scope must be one or all
- outreach.candidate_ids must be a non-empty list
- privacy.sensitive_data_stored_outside_repo must be true

## Outreach Decision

- All artist contact remains blocked; do not send a proposal request.
- Artwork and source-file requests remain blocked until a signed agreement and Gate A `PASS`.
