# Asset Gate A Check

Asset ID: truth_pen
Checked: 2026-07-26T20:10:53+09:00
Manifest: asset_pipeline/manifests/truth_pen_source_gate_a.json
Manifest SHA-256: 3f164868efef5d487d83b21f9521a0a2cd8468235adec8453f5fa59bcedb435f
Result: **FAIL**

## Findings

- source_path must select commissioned_human, openai, or cc0
- task_id must use task-NNNN format
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
- critic_review.receipt is required

## Production Decision

- `asset_factory` remains blocked for this gate.
