"""Fail-closed owner authorization for proposal-only artist outreach."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import stat
import tempfile
from copy import deepcopy
from datetime import date, datetime, timezone
from pathlib import Path
from uuid import UUID

from .asset_gate import clean_asset_id, sha256_gate_manifest
from .errors import CompanyError
from .timeutil import now_iso

PROCUREMENT_DECISION_SCHEMA = "channel_play.asset_procurement_decision.v1"
PAYMENT_ROUTES = {"upwork", "fiverr", "direct"}
SIGNER_ROLES = {"project_owner", "authorized_company_officer", "producer"}
TRUTH_PEN_CANDIDATES = {
    "cynthia_ignacio",
    "marisol_griffiths",
    "natalie_lewis",
}
SUPPORTED_CANDIDATES = {"truth_pen": TRUTH_PEN_CANDIDATES}

TOP_LEVEL_FIELDS = {
    "schema",
    "asset_id",
    "task_id",
    "decision_status",
    "owner",
    "commercial",
    "schedule",
    "outreach",
    "records",
    "privacy",
}
NESTED_FIELDS = {
    "owner": {
        "secure_record_id",
        "authorized_signer_role",
        "governing_jurisdiction",
    },
    "commercial": {
        "budget_ceiling",
        "currency",
        "payment_route",
        "tax_vendor_process_confirmed_securely",
    },
    "schedule": {
        "proposal_deadline",
        "desired_delivery_date",
        "revision_limit",
    },
    "outreach": {
        "authorized",
        "authorized_at",
        "scope",
        "candidate_ids",
        "proposal_only",
        "source_creation_blocked_until_signed_agreement_and_gate_a_pass",
    },
    "records": {
        "rfp",
        "rfp_sha256",
        "procurement_packet",
        "procurement_packet_sha256",
    },
    "privacy": {
        "private_identity_documents_in_repo",
        "tax_data_in_repo",
        "banking_data_in_repo",
        "payment_credentials_in_repo",
        "sensitive_data_stored_outside_repo",
    },
}
EXPECTED_RECORDS = {
    "truth_pen": {
        "rfp": "asset_pipeline/briefs/truth_pen_commission_rfp.md",
        "procurement_packet": "docs/research/truth_pen_artist_procurement_packet.md",
    }
}
OWNER_DECISION_FIELDS = (
    "decision_status",
    "owner.secure_record_id",
    "owner.authorized_signer_role",
    "owner.governing_jurisdiction",
    "commercial.budget_ceiling",
    "commercial.currency",
    "commercial.payment_route",
    "commercial.tax_vendor_process_confirmed_securely",
    "schedule.proposal_deadline",
    "schedule.desired_delivery_date",
    "schedule.revision_limit",
    "outreach.authorized",
    "outreach.authorized_at",
    "outreach.scope",
    "outreach.candidate_ids",
    "privacy.sensitive_data_stored_outside_repo",
)
_FIXED_SAFETY_FIELDS = (
    "outreach.proposal_only",
    "outreach.source_creation_blocked_until_signed_agreement_and_gate_a_pass",
    "privacy.private_identity_documents_in_repo",
    "privacy.tax_data_in_repo",
    "privacy.banking_data_in_repo",
    "privacy.payment_credentials_in_repo",
)
_MISSING_DECISION_VALUE = object()


def procurement_decision_init(root: Path, asset_id: str) -> Path:
    """Create a non-authorizing owner decision template without overwriting it."""
    clean = clean_asset_id(asset_id)
    _require_supported_tracked_asset(root, clean)
    manifest = procurement_manifest_path(root, clean)
    if not manifest.exists():
        _write_json(manifest, _decision_template(root, clean))
    return manifest


def procurement_outreach_check(root: Path, asset_id: str) -> Path:
    """Write an outreach receipt and fail unless every owner decision is ready."""
    clean = clean_asset_id(asset_id)
    _require_supported_tracked_asset(root, clean)
    manifest = procurement_manifest_path(root, clean)
    if not manifest.is_file():
        raise CompanyError(
            f"Procurement decision missing for {clean}. "
            f"Run: python tools/channelctl asset procurement-init {clean}"
        )
    result = evaluate_procurement_outreach(root, clean)
    receipt = _write_receipt(root, clean, result)
    if not result["passed"]:
        summary = "; ".join(result["errors"][:3])
        raise CompanyError(
            f"Proposal outreach blocked for {clean}: {summary}. "
            f"See {receipt.relative_to(root).as_posix()}"
        )
    return receipt


def evaluate_procurement_outreach(root: Path, asset_id: str) -> dict:
    """Evaluate a repository-safe owner decision without mutating any file."""
    clean = clean_asset_id(asset_id)
    manifest = procurement_manifest_path(root, clean)
    errors: list[str] = []
    data: dict = {}
    digest = ""

    if clean not in SUPPORTED_CANDIDATES:
        errors.append(f"procurement workflow is not configured for asset: {clean}")
    if not _is_tracked_asset(root, clean):
        errors.append(f"unknown asset: {clean}")
    if not manifest.is_file():
        errors.append("procurement decision manifest is missing")
        return _result(clean, manifest, data, digest, errors)

    try:
        raw = json.loads(
            manifest.read_text(encoding="utf-8"),
            parse_constant=_reject_nonfinite_json,
        )
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        errors.append(f"procurement decision is not valid UTF-8 JSON: {exc}")
        return _result(clean, manifest, data, digest, errors)
    if not isinstance(raw, dict):
        errors.append("procurement decision top level must be a JSON object")
        return _result(clean, manifest, data, digest, errors)
    data = raw
    digest = sha256_gate_manifest(manifest)
    _validate_decision(root, clean, data, errors)
    return _result(clean, manifest, data, digest, errors)


def preview_procurement_answers(
    root: Path,
    asset_id: str,
    answers: object,
) -> dict:
    """Validate owner answers in memory without changing authorization."""
    clean = clean_asset_id(asset_id)
    _require_supported_tracked_asset(root, clean)
    current, accepted_fields, candidate, errors = _prepare_answer_candidate(
        root,
        clean,
        answers,
    )
    return _preview_result(
        current,
        accepted_fields,
        candidate,
        errors,
    )


def procurement_answer_digest(answers: object) -> str:
    """Hash exactly the canonical owner answers without retaining them."""
    if not isinstance(answers, dict):
        raise CompanyError("Procurement answers must be a JSON object.")
    if (
        len(answers) != len(OWNER_DECISION_FIELDS)
        or set(answers) != set(OWNER_DECISION_FIELDS)
    ):
        raise CompanyError(
            "Procurement answers must contain every canonical owner field."
        )
    canonical = {
        field: answers[field]
        for field in OWNER_DECISION_FIELDS
    }
    try:
        encoded = json.dumps(
            canonical,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise CompanyError(
            "Procurement answers must use finite JSON values."
        ) from exc
    return hashlib.sha256(encoded).hexdigest()


def apply_procurement_answers(
    root: Path,
    asset_id: str,
    answers: object,
    expected_manifest_sha256: str,
) -> dict:
    """Atomically save validated owner answers without creating a receipt."""
    clean = clean_asset_id(asset_id)
    _require_supported_tracked_asset(root, clean)
    current, accepted_fields, candidate, errors = _prepare_answer_candidate(
        root,
        clean,
        answers,
    )
    if (
        errors
        or len(accepted_fields) != len(OWNER_DECISION_FIELDS)
        or not candidate
    ):
        raise CompanyError(
            "Owner answers must pass a complete preview before saving."
        )
    changed_fields, _, protected_state_preserved = _answer_change_summary(
        current,
        accepted_fields,
        candidate,
    )
    if not protected_state_preserved:
        raise CompanyError(
            "Protected procurement state must remain unchanged."
        )
    if not changed_fields:
        raise CompanyError(
            "Owner answers do not change the current manifest."
        )

    current_digest = str(current.get("manifest_sha256") or "")
    if (
        not expected_manifest_sha256
        or current_digest != expected_manifest_sha256
    ):
        raise CompanyError(
            "Procurement manifest changed; run the preview again."
        )
    manifest = procurement_manifest_path(root, clean)
    if (
        not manifest.is_file()
        or sha256_gate_manifest(manifest) != expected_manifest_sha256
    ):
        raise CompanyError(
            "Procurement manifest changed; run the preview again."
        )

    _write_json_atomic(manifest, candidate)
    saved_digest = sha256_gate_manifest(manifest)
    return {
        "saved": True,
        "contactAuthorized": False,
        "receiptCreated": False,
        "manifest": manifest.relative_to(root).as_posix(),
        "manifestSha256": saved_digest,
        "nextCommand": "asset.procurementCheck",
    }


def procurement_manifest_path(root: Path, asset_id: str) -> Path:
    clean = clean_asset_id(asset_id)
    return (
        root
        / "asset_pipeline"
        / "manifests"
        / f"{clean}_procurement_decision.json"
    )


def _decision_template(root: Path, asset_id: str) -> dict:
    records: dict[str, str] = {}
    for key, relative in EXPECTED_RECORDS[asset_id].items():
        path = root / relative
        if not path.is_file():
            raise CompanyError(f"Required procurement record missing: {relative}")
        records[key] = relative
        records[f"{key}_sha256"] = sha256_gate_manifest(path)
    return {
        "schema": PROCUREMENT_DECISION_SCHEMA,
        "asset_id": asset_id,
        "task_id": "task-0014",
        "decision_status": "draft",
        "owner": {
            "secure_record_id": "UNKNOWN",
            "authorized_signer_role": "UNKNOWN",
            "governing_jurisdiction": "UNKNOWN",
        },
        "commercial": {
            "budget_ceiling": 0,
            "currency": "UNKNOWN",
            "payment_route": "unselected",
            "tax_vendor_process_confirmed_securely": False,
        },
        "schedule": {
            "proposal_deadline": "UNKNOWN",
            "desired_delivery_date": "UNKNOWN",
            "revision_limit": 0,
        },
        "outreach": {
            "authorized": False,
            "authorized_at": "",
            "scope": "none",
            "candidate_ids": [],
            "proposal_only": True,
            "source_creation_blocked_until_signed_agreement_and_gate_a_pass": True,
        },
        "records": records,
        "privacy": {
            "private_identity_documents_in_repo": False,
            "tax_data_in_repo": False,
            "banking_data_in_repo": False,
            "payment_credentials_in_repo": False,
            "sensitive_data_stored_outside_repo": False,
        },
    }


def _validate_decision(
    root: Path,
    asset_id: str,
    data: dict,
    errors: list[str],
) -> None:
    _validate_keys(data, TOP_LEVEL_FIELDS, "decision", errors)
    if data.get("schema") != PROCUREMENT_DECISION_SCHEMA:
        errors.append(f"schema must be {PROCUREMENT_DECISION_SCHEMA}")
    if data.get("asset_id") != asset_id:
        errors.append(f"asset_id must be {asset_id}")
    if not re.fullmatch(r"task-\d{4}", str(data.get("task_id") or "")):
        errors.append("task_id must use task-NNNN")
    if data.get("decision_status") != "approved_for_proposal_outreach":
        errors.append("decision_status must be approved_for_proposal_outreach")

    sections: dict[str, dict] = {}
    for name, expected in NESTED_FIELDS.items():
        value = data.get(name)
        if not isinstance(value, dict):
            errors.append(f"{name} must be an object")
            sections[name] = {}
            continue
        sections[name] = value
        _validate_keys(value, expected, name, errors)

    _validate_owner(sections["owner"], errors)
    _validate_commercial(sections["commercial"], errors)
    _validate_schedule(sections["schedule"], errors)
    _validate_outreach(asset_id, sections["outreach"], errors)
    _validate_records(root, asset_id, sections["records"], errors)
    _validate_privacy(sections["privacy"], errors)


def _validate_owner(owner: dict, errors: list[str]) -> None:
    record_id = str(owner.get("secure_record_id") or "")
    if not _is_canonical_vault_id(record_id):
        errors.append(
            "owner.secure_record_id must use vault:<canonical-lowercase-UUID>"
        )
    if owner.get("authorized_signer_role") not in SIGNER_ROLES:
        errors.append(
            "owner.authorized_signer_role must be project_owner, "
            "authorized_company_officer, or producer"
        )
    jurisdiction = str(owner.get("governing_jurisdiction") or "")
    if not re.fullmatch(r"[A-Z]{2}(?:-[A-Z0-9]{1,12})?", jurisdiction):
        errors.append(
            "owner.governing_jurisdiction must use a repository-safe code "
            "such as KR or US-CA"
        )


def _validate_commercial(commercial: dict, errors: list[str]) -> None:
    budget = commercial.get("budget_ceiling")
    if (
        isinstance(budget, bool)
        or not isinstance(budget, (int, float))
        or not math.isfinite(float(budget))
        or budget <= 0
    ):
        errors.append(
            "commercial.budget_ceiling must be a positive finite number"
        )
    if not re.fullmatch(r"[A-Z]{3}", str(commercial.get("currency") or "")):
        errors.append("commercial.currency must be a three-letter currency code")
    if commercial.get("payment_route") not in PAYMENT_ROUTES:
        errors.append("commercial.payment_route must be upwork, fiverr, or direct")
    if commercial.get("tax_vendor_process_confirmed_securely") is not True:
        errors.append(
            "commercial.tax_vendor_process_confirmed_securely must be true"
        )


def _validate_schedule(schedule: dict, errors: list[str]) -> None:
    proposal = _parse_date(
        schedule.get("proposal_deadline"),
        "schedule.proposal_deadline",
        errors,
    )
    delivery = _parse_date(
        schedule.get("desired_delivery_date"),
        "schedule.desired_delivery_date",
        errors,
    )
    if proposal is not None and proposal < date.today():
        errors.append("schedule.proposal_deadline must not be in the past")
    if proposal is not None and delivery is not None and delivery <= proposal:
        errors.append(
            "schedule.desired_delivery_date must be after proposal_deadline"
        )
    revision_limit = schedule.get("revision_limit")
    if (
        isinstance(revision_limit, bool)
        or not isinstance(revision_limit, int)
        or not 1 <= revision_limit <= 10
    ):
        errors.append("schedule.revision_limit must be an integer from 1 to 10")


def _validate_outreach(
    asset_id: str,
    outreach: dict,
    errors: list[str],
) -> None:
    if outreach.get("authorized") is not True:
        errors.append("outreach.authorized must be true")
    _parse_authorized_at(outreach.get("authorized_at"), errors)

    scope = outreach.get("scope")
    if scope not in {"one", "all"}:
        errors.append("outreach.scope must be one or all")
    candidates = outreach.get("candidate_ids")
    allowed = SUPPORTED_CANDIDATES.get(asset_id, set())
    if not isinstance(candidates, list) or not candidates:
        errors.append("outreach.candidate_ids must be a non-empty list")
    elif not all(isinstance(candidate, str) for candidate in candidates):
        errors.append("outreach.candidate_ids entries must be strings")
    else:
        if len(candidates) != len(set(candidates)):
            errors.append("outreach.candidate_ids must not contain duplicates")
        unknown = sorted(set(candidates) - allowed)
        if unknown:
            errors.append(
                "outreach.candidate_ids contains unknown candidates: "
                + ", ".join(unknown)
            )
        if scope == "one" and len(candidates) != 1:
            errors.append("outreach.scope one requires exactly one candidate")
        if scope == "all" and set(candidates) != allowed:
            errors.append("outreach.scope all requires every shortlisted candidate")
    if outreach.get("proposal_only") is not True:
        errors.append("outreach.proposal_only must be true")
    if (
        outreach.get(
            "source_creation_blocked_until_signed_agreement_and_gate_a_pass"
        )
        is not True
    ):
        errors.append(
            "outreach must keep source creation blocked until a signed "
            "agreement and Gate A pass"
        )


def _validate_records(
    root: Path,
    asset_id: str,
    records: dict,
    errors: list[str],
) -> None:
    expected = EXPECTED_RECORDS.get(asset_id, {})
    for key, expected_path in expected.items():
        value = records.get(key)
        if value != expected_path:
            errors.append(f"records.{key} must be {expected_path}")
            continue
        path = root / expected_path
        if not path.is_file():
            errors.append(f"records.{key} does not exist: {expected_path}")
            continue
        expected_hash = sha256_gate_manifest(path)
        hash_key = f"{key}_sha256"
        if records.get(hash_key) != expected_hash:
            errors.append(
                f"records.{hash_key} must match current {key}: {expected_hash}"
            )


def _validate_privacy(privacy: dict, errors: list[str]) -> None:
    for field in (
        "private_identity_documents_in_repo",
        "tax_data_in_repo",
        "banking_data_in_repo",
        "payment_credentials_in_repo",
    ):
        if privacy.get(field) is not False:
            errors.append(f"privacy.{field} must be false")
    if privacy.get("sensitive_data_stored_outside_repo") is not True:
        errors.append("privacy.sensitive_data_stored_outside_repo must be true")


def _validate_keys(
    data: dict,
    expected: set[str],
    label: str,
    errors: list[str],
) -> None:
    for missing in sorted(expected - set(data)):
        errors.append(f"{label}.{missing} is required")
    for unexpected in sorted(set(data) - expected):
        errors.append(f"{label} contains unsupported field: {unexpected}")


def _parse_date(value: object, label: str, errors: list[str]) -> date | None:
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        errors.append(f"{label} must use YYYY-MM-DD")
        return None


def _parse_authorized_at(value: object, errors: list[str]) -> None:
    text = str(value or "")
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        errors.append("outreach.authorized_at must be an ISO-8601 timestamp")
        return
    if parsed.tzinfo is None:
        errors.append("outreach.authorized_at must include a UTC offset")
        return
    if parsed > datetime.now(timezone.utc):
        errors.append("outreach.authorized_at must not be in the future")


def _is_canonical_vault_id(value: str) -> bool:
    if not value.startswith("vault:"):
        return False
    identifier = value.removeprefix("vault:")
    try:
        parsed = UUID(identifier)
    except ValueError:
        return False
    return str(parsed) == identifier


def _reject_nonfinite_json(value: str) -> None:
    raise ValueError(f"non-standard numeric constant is prohibited: {value}")


def _contains_nonfinite(value: object) -> bool:
    if isinstance(value, float):
        return not math.isfinite(value)
    if isinstance(value, dict):
        return any(_contains_nonfinite(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_contains_nonfinite(item) for item in value)
    return False


def _prepare_answer_candidate(
    root: Path,
    asset_id: str,
    answers: object,
) -> tuple[dict, list[str], dict, list[str]]:
    if not isinstance(answers, dict):
        raise CompanyError("Procurement preview answers must be a JSON object.")

    current = evaluate_procurement_outreach(root, asset_id)
    current_data = current.get("data")
    if not isinstance(current_data, dict) or not current_data:
        return (
            current,
            [],
            {},
            [
                "current procurement manifest must be valid JSON before "
                "answer preview"
            ],
        )

    allowed = set(OWNER_DECISION_FIELDS)
    accepted_fields = [
        field for field in OWNER_DECISION_FIELDS if field in answers
    ]
    unsupported_count = sum(
        1
        for field in answers
        if not isinstance(field, str) or field not in allowed
    )
    errors: list[str] = []
    if unsupported_count:
        errors.append(
            "answers contain "
            f"{unsupported_count} unsupported field(s); only canonical owner "
            "decision fields are allowed"
        )
    if _contains_nonfinite(answers):
        errors.append("answers contain a non-finite numeric value")

    candidate = deepcopy(current_data)
    for field in accepted_fields:
        _set_decision_field(candidate, field, deepcopy(answers[field]))
    validation_errors: list[str] = []
    _validate_decision(root, asset_id, candidate, validation_errors)
    errors.extend(_redact_preview_error(error) for error in validation_errors)
    return current, accepted_fields, candidate, errors


def _set_decision_field(data: dict, field: str, value: object) -> None:
    if "." not in field:
        data[field] = value
        return
    section, key = field.split(".", 1)
    target = data.get(section)
    if not isinstance(target, dict):
        target = {}
        data[section] = target
    target[key] = value


def _decision_field_value(data: dict, field: str) -> object:
    if "." not in field:
        return data.get(field, _MISSING_DECISION_VALUE)
    section, key = field.split(".", 1)
    target = data.get(section)
    if not isinstance(target, dict):
        return _MISSING_DECISION_VALUE
    return target.get(key, _MISSING_DECISION_VALUE)


def _json_values_equal(left: object, right: object) -> bool:
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return (
            left.keys() == right.keys()
            and all(
                _json_values_equal(left[key], right[key])
                for key in left
            )
        )
    if isinstance(left, list):
        return (
            len(left) == len(right)
            and all(
                _json_values_equal(left_item, right_item)
                for left_item, right_item in zip(left, right)
            )
        )
    return left == right


def _answer_change_summary(
    current: dict,
    accepted_fields: list[str],
    candidate: dict,
) -> tuple[list[str], list[str], bool]:
    current_data = current.get("data")
    if not isinstance(current_data, dict) or not candidate:
        return [], [], False

    changed_fields = [
        field
        for field in accepted_fields
        if not _json_values_equal(
            _decision_field_value(current_data, field),
            _decision_field_value(candidate, field),
        )
    ]
    unchanged_fields = [
        field
        for field in accepted_fields
        if field not in changed_fields
    ]
    protected_state_preserved = (
        current_data.get("records", _MISSING_DECISION_VALUE)
        == candidate.get("records", _MISSING_DECISION_VALUE)
        and all(
            _decision_field_value(current_data, field)
            == _decision_field_value(candidate, field)
            for field in _FIXED_SAFETY_FIELDS
        )
    )
    return changed_fields, unchanged_fields, protected_state_preserved


def _redact_preview_error(error: str) -> str:
    if error.startswith(
        "outreach.candidate_ids contains unknown candidates:"
    ):
        return "outreach.candidate_ids contains unsupported candidate IDs"
    return error


def _preview_result(
    current: dict,
    accepted_fields: list[str],
    candidate: dict,
    errors: list[str],
) -> dict:
    missing_fields = [
        field
        for field in OWNER_DECISION_FIELDS
        if field not in accepted_fields
    ]
    (
        changed_fields,
        unchanged_fields,
        protected_state_preserved,
    ) = _answer_change_summary(
        current,
        accepted_fields,
        candidate,
    )
    return {
        "previewOnly": True,
        "valid": not errors,
        "contactAuthorized": False,
        "receiptCreated": False,
        "answerCount": len(accepted_fields),
        "expectedAnswerCount": len(OWNER_DECISION_FIELDS),
        "acceptedFields": accepted_fields,
        "missingFields": missing_fields,
        "changeCount": len(changed_fields),
        "unchangedCount": len(unchanged_fields),
        "changedFields": changed_fields,
        "unchangedFields": unchanged_fields,
        "protectedStatePreserved": protected_state_preserved,
        "errorCount": len(errors),
        "errors": errors,
        "manifestSha256": str(current.get("manifest_sha256") or ""),
    }


def _require_supported_tracked_asset(root: Path, asset_id: str) -> None:
    if asset_id not in SUPPORTED_CANDIDATES:
        raise CompanyError(
            f"Procurement workflow is not configured for asset: {asset_id}"
        )
    if not _is_tracked_asset(root, asset_id):
        raise CompanyError(f"Unknown asset: {asset_id}")


def _is_tracked_asset(root: Path, asset_id: str) -> bool:
    index = root / "asset_pipeline" / "index.json"
    if not index.is_file():
        return False
    try:
        data = json.loads(index.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return False
    if not isinstance(data, dict):
        return False
    assets = data.get("assets")
    return isinstance(assets, list) and any(
        isinstance(item, dict) and item.get("id") == asset_id for item in assets
    )


def _write_receipt(root: Path, asset_id: str, result: dict) -> Path:
    receipt = (
        root
        / "runs"
        / f"asset-procurement-{asset_id}"
        / "outreach_readiness_check.md"
    )
    receipt.parent.mkdir(parents=True, exist_ok=True)
    outcome = "PASS" if result["passed"] else "FAIL"
    decision = (
        "- Proposal-only outreach is authorized for the recorded candidate IDs."
        if result["passed"]
        else "- All artist contact remains blocked; do not send a proposal request."
    )
    lines = [
        "# Asset Procurement Outreach Readiness",
        "",
        f"Asset ID: {asset_id}",
        f"Checked: {now_iso()}",
        f"Decision: {result['manifest'].relative_to(root).as_posix()}",
        f"Decision SHA-256: {result['manifest_sha256'] or 'unavailable'}",
        f"Result: **{outcome}**",
        "",
        "## Findings",
        "",
    ]
    lines.extend(
        (f"- {error}" for error in result["errors"])
        if result["errors"]
        else ["- Owner decisions and repository privacy controls passed."]
    )
    lines.extend(
        [
            "",
            "## Outreach Decision",
            "",
            decision,
            "- Artwork and source-file requests remain blocked until a signed "
            "agreement and Gate A `PASS`.",
            "",
        ]
    )
    receipt.write_text("\n".join(lines), encoding="utf-8")
    return receipt


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _write_json_atomic(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    original_mode = (
        stat.S_IMODE(path.stat().st_mode)
        if path.exists()
        else None
    )
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=path.parent,
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        if original_mode is not None:
            os.chmod(temporary_path, original_mode)
        os.replace(temporary_path, path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _result(
    asset_id: str,
    manifest: Path,
    data: dict,
    digest: str,
    errors: list[str],
) -> dict:
    return {
        "passed": not errors,
        "asset_id": asset_id,
        "manifest": manifest,
        "manifest_sha256": digest,
        "data": data,
        "errors": errors,
    }
