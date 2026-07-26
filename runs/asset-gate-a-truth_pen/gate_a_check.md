# Asset Gate A Check

Asset ID: truth_pen
Checked: 2026-07-26T21:33:26+09:00
Manifest: asset_pipeline/manifests/truth_pen_source_gate_a.json
Manifest SHA-256: 0595bc27b1274e73d271b713cc50b0d3f581bdcad5d530448eeb4c810c7620f2
Result: **FAIL**

## Findings

- applicable_jurisdiction is required
- provider_or_source is required
- creator_or_affirmer is required
- rights_holder_or_legal_customer is required
- license_or_agreement is required
- retrieval_date is required
- source_reference is required
- controlling_terms_reference is required
- rights.commercial_use must be PASS
- rights.derivatives must be PASS
- rights.redistribution must be PASS
- rights.marketing must be PASS
- input_clearance.project_owned_or_cleared_inputs must be true
- input_clearance.unverified_web_references must be false
- input_clearance.watermarks_or_logos must be false
- input_clearance.copied_franchise_style must be false
- input_clearance.tracing_or_image_conditioning must be false
- evidence_paths must include at least one repository evidence path
- path_details.contracting_parties is required
- path_details.signed_rights_instrument is required
- path_details.downstream_asset_creation_grant must be true
- critic_review.receipt is required

## Production Decision

- `asset_factory` remains blocked for this gate.
