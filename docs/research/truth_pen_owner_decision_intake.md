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

### 승인 상태

- `decision_status`: 소유자가 기존 서면 RFP의 제안 전송만 승인한 뒤
  `approved_for_proposal_outreach`로 변경합니다.

### 소유자 및 권한

- `owner.secure_record_id`: 개인정보 대신 보안 시스템의
  `vault:<canonical-lowercase-UUID>` 식별자만 기록합니다.
- `owner.authorized_signer_role`: `project_owner`,
  `authorized_company_officer`, `producer` 중 하나를 선택합니다.
- `owner.governing_jurisdiction`: `KR`, `US-CA`처럼 저장소에 공개 가능한
  짧은 코드를 기록합니다.

### 예산 및 결제

- `commercial.budget_ceiling`: 승인된 0보다 큰 유한 숫자를 기록합니다.
- `commercial.currency`: `KRW`, `USD`처럼 대문자 3자리 코드를 사용합니다.
- `commercial.payment_route`: `upwork`, `fiverr`, `direct` 중 선택합니다.
- `commercial.tax_vendor_process_confirmed_securely`: 민감정보를 저장소
  밖에서 처리할 절차가 확인된 경우에만 `true`로 설정합니다.

### 일정

- `schedule.proposal_deadline`: 과거가 아닌 `YYYY-MM-DD` 날짜입니다.
- `schedule.desired_delivery_date`: 제안 마감일보다 뒤인 날짜입니다.
- `schedule.revision_limit`: 승인된 1~10 사이의 정수입니다.

### 연락 범위 및 승인

- `outreach.authorized`: 제안 전송을 명시적으로 승인한 경우에만 `true`.
- `outreach.authorized_at`: 실제 승인 시각을 시간대 포함 ISO-8601로 기록.
- `outreach.scope`: 후보 1명이면 `one`, 전체 후보면 `all`.
- `outreach.candidate_ids`: 소유자가 승인한 공개 후보 ID만 기록합니다.

### 보안 및 개인정보

- `privacy.sensitive_data_stored_outside_repo`: 신원·세무·결제 자료가 승인된
  보안 시스템에만 있는 경우 `true`로 설정합니다.

## Studio Progress Meaning

Production Cockpit calculates completion from the 16 canonical fields above.
This is structural field progress only; even `16/16` does not authorize contact
without a current PASS receipt. If malformed JSON, unsupported fields, or other
unmapped validation errors exist, Studio shows `확인 필요` instead of guessing
completion.

Studio can copy a response worksheet for the currently unresolved canonical
fields. The worksheet contains field names, repository-safe guidance, and
blank placeholders only; it deliberately omits stored values and validator
messages. The copy action is disabled when progress is complete or when
malformed or unsupported data makes progress indeterminate. Copying the
worksheet does not edit the manifest, authorize contact, or create a receipt.

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
