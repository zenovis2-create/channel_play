"""Fail-closed source and production authorization gates for assets."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from .errors import CompanyError
from .timeutil import now_iso

GATE_A_SCHEMA = "channel_play.asset_source_gate_a.v1"
GATE_B_SCHEMA = "channel_play.asset_production_gate_b.v1"
CRITIC_APPROVAL_SCHEMA = "channel_play.critic_gate_approval.v1"
SOURCE_PATHS = {"unselected", "commissioned_human", "openai", "cc0"}
OPENAI_ACCOUNT_TYPES = {"chatgpt_individual", "api_business", "enterprise"}
PRODUCTION_PROVIDERS = {"rodin25", "pixal3d", "trellis2", "tripo", "local"}
RIGHT_FIELDS = ("commercial_use", "derivatives", "redistribution", "marketing")
PROHIBITED_INPUT_FIELDS = (
    "unverified_web_references",
    "watermarks_or_logos",
    "copied_franchise_style",
    "tracing_or_image_conditioning",
)


def asset_gate_a_init(root: Path, asset_id: str, *, source_path: str = "unselected") -> Path:
    """Create or select a non-approved Gate A record without erasing evidence."""
    clean = clean_asset_id(asset_id)
    selected = source_path.strip().lower() or "unselected"
    if selected not in SOURCE_PATHS:
        raise CompanyError(f"Invalid Gate A source path: {source_path}")

    manifest = gate_a_manifest_path(root, clean)
    manifest.parent.mkdir(parents=True, exist_ok=True)
    created = not manifest.exists()
    if created:
        _write_json(manifest, _gate_a_template(clean, selected))
    elif selected != "unselected":
        existing = _read_json_object(manifest, "Existing Gate A manifest")
        current = str(existing.get("source_path") or "unselected").strip().lower()
        if current not in {"unselected", selected}:
            raise CompanyError(
                f"Gate A source path is already {current}; edit the manifest "
                "explicitly before changing strategies"
            )
        if current == "unselected":
            existing["source_path"] = selected
            existing["path_details"] = _gate_a_template(clean, selected)["path_details"]
            _write_json(manifest, existing)

    result = evaluate_asset_gate_a(root, clean)
    existing_status = _index_gate_status(root, clean, "source")
    gate_status = (
        "approved"
        if result["passed"]
        else "blocked"
        if not created and existing_status == "blocked"
        else "pending"
    )
    _update_gate_index(
        root,
        clean,
        gate="source",
        gate_status=gate_status,
        manifest=manifest,
        receipt=None,
        errors=result["errors"] if gate_status == "blocked" else [],
        allow_create=True,
    )
    return manifest


def asset_gate_a_check(root: Path, asset_id: str) -> Path:
    """Validate Gate A and persist a receipt without changing lifecycle status."""
    clean = clean_asset_id(asset_id)
    _require_tracked_asset(root, clean)
    manifest = gate_a_manifest_path(root, clean)
    if not manifest.is_file():
        raise CompanyError(
            f"Gate A manifest missing for {clean}. "
            f"Run: python tools/channelctl asset gate-a-init {clean}"
        )
    result = evaluate_asset_gate_a(root, clean)
    receipt = _write_gate_receipt(root, clean, "A", result)
    _update_gate_index(
        root,
        clean,
        gate="source",
        gate_status="approved" if result["passed"] else "blocked",
        manifest=manifest,
        receipt=receipt,
        errors=result["errors"],
        allow_create=False,
    )
    if not result["passed"]:
        raise CompanyError(_blocked_message("Gate A", clean, result, receipt, root))
    return receipt


def asset_gate_b_init(root: Path, asset_id: str) -> Path:
    """Create a Gate B record only after the exact Gate A record passes."""
    clean = clean_asset_id(asset_id)
    _require_tracked_asset(root, clean)
    require_asset_gate_a(root, clean)
    manifest = gate_b_manifest_path(root, clean)
    if not manifest.exists():
        gate_a_manifest = gate_a_manifest_path(root, clean)
        gate_a_data = _read_json_object(gate_a_manifest, "Gate A manifest")
        _write_json(
            manifest,
            _gate_b_template(
                clean,
                str(gate_a_data.get("task_id") or ""),
                gate_a_manifest.relative_to(root).as_posix(),
                sha256_gate_manifest(gate_a_manifest),
            ),
        )
    result = evaluate_asset_gate_b(root, clean)
    _update_gate_index(
        root,
        clean,
        gate="production",
        gate_status="approved" if result["passed"] else "pending",
        manifest=manifest,
        receipt=None,
        errors=[],
        allow_create=False,
    )
    return manifest


def asset_gate_b_check(root: Path, asset_id: str) -> Path:
    """Validate Gate B and persist a production authorization receipt."""
    clean = clean_asset_id(asset_id)
    _require_tracked_asset(root, clean)
    manifest = gate_b_manifest_path(root, clean)
    if not manifest.is_file():
        raise CompanyError(
            f"Gate B manifest missing for {clean}. "
            f"Run: python tools/channelctl asset gate-b-init {clean}"
        )
    result = evaluate_asset_gate_b(root, clean)
    receipt = _write_gate_receipt(root, clean, "B", result)
    _update_gate_index(
        root,
        clean,
        gate="production",
        gate_status="approved" if result["passed"] else "blocked",
        manifest=manifest,
        receipt=receipt,
        errors=result["errors"],
        allow_create=False,
    )
    if not result["passed"]:
        raise CompanyError(_blocked_message("Gate B", clean, result, receipt, root))
    return receipt


def require_asset_gate_a(root: Path, asset_id: str) -> dict:
    """Authorize source creation or download, never 3D production."""
    clean = clean_asset_id(asset_id)
    result = evaluate_asset_gate_a(root, clean)
    if result["passed"]:
        return result
    command = "gate-a-check" if result["manifest"].exists() else "gate-a-init"
    summary = "; ".join(result["errors"][:3])
    raise CompanyError(
        f"Gate A approval required before source creation for {clean}: {summary}. "
        f"Run: python tools/channelctl asset {command} {clean}"
    )


def require_asset_gate_b(
    root: Path,
    asset_id: str,
    *,
    provider: str | None = None,
) -> dict:
    """Authorize 3D generation, cleanup, Unity copy/import, or acceptance."""
    clean = clean_asset_id(asset_id)
    result = evaluate_asset_gate_b(root, clean)
    if not result["passed"]:
        command = "gate-b-check" if result["manifest"].exists() else "gate-b-init"
        summary = "; ".join(result["errors"][:3])
        raise CompanyError(
            f"Gate B approval required before production for {clean}: {summary}. "
            f"Run: python tools/channelctl asset {command} {clean}"
        )
    approved_provider = result["data"]["production"]["approved_3d_provider"]
    if provider is not None and provider != approved_provider:
        raise CompanyError(
            f"Gate B approves provider {approved_provider}, not {provider}; "
            "auto, both, and unreviewed fallback providers are prohibited"
        )
    return result


def evaluate_asset_gate_a(root: Path, asset_id: str) -> dict:
    """Return a deterministic Gate A result without mutating state."""
    clean = clean_asset_id(asset_id)
    manifest = gate_a_manifest_path(root, clean)
    data, errors = _load_manifest(manifest, GATE_A_SCHEMA, clean)
    if data is None:
        return _result(clean, "A", "unselected", manifest, None, errors)

    source_path = str(data.get("source_path") or "").strip().lower()
    if source_path not in SOURCE_PATHS - {"unselected"}:
        errors.append("source_path must select commissioned_human, openai, or cc0")
    _validate_task_id(data.get("task_id"), errors)
    _require_text(data, "applicable_jurisdiction", errors)
    for field in (
        "provider_or_source",
        "creator_or_affirmer",
        "rights_holder_or_legal_customer",
        "license_or_agreement",
    ):
        _require_text(data, field, errors)
    retrieval_date = _validate_date(data.get("retrieval_date"), "retrieval_date", errors)
    _validate_reference(root, data.get("source_reference"), "source_reference", errors)
    _validate_reference(
        root,
        data.get("controlling_terms_reference"),
        "controlling_terms_reference",
        errors,
    )
    _validate_rights(data.get("rights"), errors)
    _validate_input_clearance(data.get("input_clearance"), errors)
    _validate_evidence_paths(root, data.get("evidence_paths"), "evidence_paths", errors)

    details = data.get("path_details")
    if not isinstance(details, dict):
        errors.append("path_details must be an object")
        details = {}
    if source_path == "commissioned_human":
        _validate_human_path(root, details, errors)
    elif source_path == "openai":
        _validate_openai_path(root, data, details, errors)
    elif source_path == "cc0":
        _validate_cc0_path(root, details, errors)

    _validate_gate_approval(
        root,
        data.get("critic_review"),
        manifest=manifest,
        asset_id=clean,
        task_id=str(data.get("task_id") or ""),
        gate="A",
        minimum_date=retrieval_date,
        errors=errors,
    )
    return _result(clean, "A", source_path or "unselected", manifest, data, errors)


def evaluate_asset_gate_b(root: Path, asset_id: str) -> dict:
    """Return a deterministic Gate B result without mutating state."""
    clean = clean_asset_id(asset_id)
    manifest = gate_b_manifest_path(root, clean)
    data, errors = _load_manifest(manifest, GATE_B_SCHEMA, clean)
    if data is None:
        return _result(clean, "B", "production", manifest, None, errors)

    _validate_task_id(data.get("task_id"), errors)
    gate_a_result = evaluate_asset_gate_a(root, clean)
    if not gate_a_result["passed"]:
        errors.append("Gate A must still pass before Gate B")
    gate_a_ref = _repo_file(
        root,
        data.get("gate_a_manifest"),
        "gate_a_manifest",
        errors,
    )
    expected_gate_a = gate_a_manifest_path(root, clean).resolve()
    if gate_a_ref is not None and gate_a_ref.resolve() != expected_gate_a:
        errors.append("gate_a_manifest must reference this asset's canonical Gate A manifest")
    if gate_a_ref is not None:
        expected_hash = sha256_gate_manifest(gate_a_ref)
        if data.get("gate_a_manifest_sha256") != expected_hash:
            errors.append("gate_a_manifest_sha256 does not match the current Gate A manifest")

    source = _repo_file(root, data.get("source_asset_path"), "source_asset_path", errors)
    if source is not None and data.get("source_sha256") != sha256_file(source):
        errors.append("source_sha256 does not match source_asset_path")
    acquired_at = _validate_datetime(
        data.get("source_created_or_acquired_at"),
        "source_created_or_acquired_at",
        errors,
    )
    for field in (
        "prompt_record",
        "edit_history_record",
        "clearance_record",
        "attribution_disclosure_record",
    ):
        _repo_file(root, data.get(field), field, errors)
    _require_text(data, "source_provider_or_tool", errors)
    _require_text(data, "source_model_or_version", errors)
    _validate_rights(data.get("rights"), errors)

    production = data.get("production")
    if not isinstance(production, dict):
        errors.append("production must be an object")
    else:
        provider = str(production.get("approved_3d_provider") or "").strip().lower()
        if provider not in PRODUCTION_PROVIDERS:
            errors.append(
                "production.approved_3d_provider must select rodin25, pixal3d, "
                "trellis2, tripo, or local"
            )
        if production.get("allow_unreviewed_fallback") is not False:
            errors.append("production.allow_unreviewed_fallback must be false")

    _validate_gate_approval(
        root,
        data.get("critic_review"),
        manifest=manifest,
        asset_id=clean,
        task_id=str(data.get("task_id") or ""),
        gate="B",
        minimum_date=acquired_at.date() if acquired_at else None,
        errors=errors,
    )
    return _result(clean, "B", "production", manifest, data, errors)


def approved_gate_b_source(root: Path, asset_id: str, *, provider: str) -> Path:
    """Return the exact source file bound to an approved production gate."""
    result = require_asset_gate_b(root, asset_id, provider=provider)
    return (root / result["data"]["source_asset_path"]).resolve()


def gate_a_manifest_path(root: Path, asset_id: str) -> Path:
    return root / "asset_pipeline" / "manifests" / f"{asset_id}_source_gate_a.json"


def gate_b_manifest_path(root: Path, asset_id: str) -> Path:
    return root / "asset_pipeline" / "manifests" / f"{asset_id}_production_gate_b.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_gate_manifest(path: Path) -> str:
    """Hash a UTF-8 gate record without platform-specific line endings."""
    text = path.read_text(encoding="utf-8")
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def clean_asset_id(asset_id: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9_-]+", "_", asset_id.strip()).strip("_").lower()
    if not clean:
        raise CompanyError("asset id required")
    return clean


def _gate_a_template(asset_id: str, source_path: str) -> dict:
    details: dict[str, object] = {}
    if source_path == "commissioned_human":
        details = {
            "contracting_parties": "",
            "signed_rights_instrument": "",
            "downstream_asset_creation_grant": None,
        }
    elif source_path == "openai":
        details = {
            "product_account_type": "",
            "workspace_owner": "",
            "intended_model": "",
            "beta_service": None,
            "beta_risk_acceptance": "",
            "producing_contributor": "",
            "contributor_transfer_evidence": "",
            "input_rights_evidence": "",
            "non_uniqueness_acknowledged": None,
            "human_review_required": None,
            "output_allocation_not_warranty": None,
            "indemnity_limits_reviewed": None,
            "ai_provenance_record": "",
            "disclosure_decision_record": "",
            "public_service_sharing": None,
            "third_party_app_or_gpt": None,
            "likeness_or_real_person": None,
        }
    elif source_path == "cc0":
        details = {
            "exact_work_url": "",
            "original_host": "",
            "cc0_marking_url": "",
            "retrieval_snapshot": "",
            "affirmer_authority_evidence": "",
        }
    return {
        "schema": GATE_A_SCHEMA,
        "asset_id": asset_id,
        "task_id": "",
        "source_path": source_path,
        "applicable_jurisdiction": "",
        "provider_or_source": "",
        "creator_or_affirmer": "",
        "rights_holder_or_legal_customer": "",
        "license_or_agreement": "",
        "source_reference": "",
        "retrieval_date": "",
        "controlling_terms_reference": "",
        "rights": {field: "UNKNOWN" for field in RIGHT_FIELDS},
        "input_clearance": {
            "project_owned_or_cleared_inputs": None,
            **{field: None for field in PROHIBITED_INPUT_FIELDS},
        },
        "path_details": details,
        "evidence_paths": [],
        "critic_review": {"receipt": ""},
    }


def _gate_b_template(
    asset_id: str,
    gate_a_task_id: str,
    gate_a_manifest: str,
    gate_a_hash: str,
) -> dict:
    return {
        "schema": GATE_B_SCHEMA,
        "asset_id": asset_id,
        "task_id": "",
        "gate_a_task_id": gate_a_task_id,
        "gate_a_manifest": gate_a_manifest,
        "gate_a_manifest_sha256": gate_a_hash,
        "source_asset_path": "",
        "source_sha256": "",
        "source_created_or_acquired_at": "",
        "source_provider_or_tool": "",
        "source_model_or_version": "",
        "source_job_or_seed": "",
        "prompt_record": "",
        "edit_history_record": "",
        "clearance_record": "",
        "attribution_disclosure_record": "",
        "rights": {field: "UNKNOWN" for field in RIGHT_FIELDS},
        "production": {
            "approved_3d_provider": "",
            "allow_unreviewed_fallback": None,
        },
        "critic_review": {"receipt": ""},
    }


def _load_manifest(
    manifest: Path,
    schema: str,
    asset_id: str,
) -> tuple[dict | None, list[str]]:
    if not manifest.exists():
        return None, [f"{manifest.name} is missing"]
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, [f"{manifest.name} is unreadable: {exc}"]
    if not isinstance(data, dict):
        return None, [f"{manifest.name} top level must be a JSON object"]
    errors: list[str] = []
    if data.get("schema") != schema:
        errors.append(f"schema must be {schema}")
    if data.get("asset_id") != asset_id:
        errors.append(f"asset_id must be {asset_id}")
    return data, errors


def _validate_human_path(root: Path, details: dict, errors: list[str]) -> None:
    _require_text(details, "contracting_parties", errors, prefix="path_details.")
    _repo_file(
        root,
        details.get("signed_rights_instrument"),
        "path_details.signed_rights_instrument",
        errors,
    )
    if details.get("downstream_asset_creation_grant") is not True:
        errors.append("path_details.downstream_asset_creation_grant must be true")


def _validate_openai_path(root: Path, data: dict, details: dict, errors: list[str]) -> None:
    account_type = str(details.get("product_account_type") or "").strip()
    if account_type not in OPENAI_ACCOUNT_TYPES:
        errors.append(
            "path_details.product_account_type must be chatgpt_individual, "
            "api_business, or enterprise"
        )
    for field in ("workspace_owner", "intended_model", "producing_contributor"):
        _require_text(details, field, errors, prefix="path_details.")
    beta_service = details.get("beta_service")
    if not isinstance(beta_service, bool):
        errors.append("path_details.beta_service must be true or false")
    elif beta_service:
        _repo_file(
            root,
            details.get("beta_risk_acceptance"),
            "path_details.beta_risk_acceptance",
            errors,
        )
    for field in (
        "contributor_transfer_evidence",
        "input_rights_evidence",
        "ai_provenance_record",
        "disclosure_decision_record",
    ):
        _repo_file(root, details.get(field), f"path_details.{field}", errors)
    for field in (
        "non_uniqueness_acknowledged",
        "human_review_required",
        "output_allocation_not_warranty",
        "indemnity_limits_reviewed",
    ):
        if details.get(field) is not True:
            errors.append(f"path_details.{field} must be true")
    for field in (
        "public_service_sharing",
        "third_party_app_or_gpt",
        "likeness_or_real_person",
    ):
        if details.get(field) is not False:
            errors.append(f"path_details.{field} must be false")
    terms = urlparse(str(data.get("controlling_terms_reference") or ""))
    if terms.hostname not in {"openai.com", "www.openai.com"}:
        errors.append("OpenAI path controlling_terms_reference must use openai.com")


def _validate_cc0_path(root: Path, details: dict, errors: list[str]) -> None:
    _validate_https_url(details.get("exact_work_url"), "path_details.exact_work_url", errors)
    _require_text(details, "original_host", errors, prefix="path_details.")
    _validate_https_url(details.get("cc0_marking_url"), "path_details.cc0_marking_url", errors)
    marking = urlparse(str(details.get("cc0_marking_url") or ""))
    if marking.hostname not in {"creativecommons.org", "www.creativecommons.org"}:
        errors.append("path_details.cc0_marking_url must use creativecommons.org")
    for field in ("retrieval_snapshot", "affirmer_authority_evidence"):
        _repo_file(root, details.get(field), f"path_details.{field}", errors)


def _validate_gate_approval(
    root: Path,
    value: object,
    *,
    manifest: Path,
    asset_id: str,
    task_id: str,
    gate: str,
    minimum_date: date | None,
    errors: list[str],
) -> None:
    if not isinstance(value, dict):
        errors.append("critic_review must be an object")
        return
    receipt = _repo_file(root, value.get("receipt"), "critic_review.receipt", errors)
    if receipt is None:
        return
    try:
        approval = json.loads(receipt.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"critic_review.receipt is unreadable JSON: {exc}")
        return
    if not isinstance(approval, dict):
        errors.append("critic_review.receipt top level must be a JSON object")
        return
    expected = {
        "schema": CRITIC_APPROVAL_SCHEMA,
        "asset_id": asset_id,
        "task_id": task_id,
        "gate": gate,
        "manifest_sha256": sha256_gate_manifest(manifest),
        "reviewer_role": "critic_reviewer",
        "verdict": "APPROVED",
    }
    for field, expected_value in expected.items():
        if approval.get(field) != expected_value:
            errors.append(f"critic approval {field} must be {expected_value}")
    if gate == "A":
        if approval.get("source_creation_authorized") is not True:
            errors.append("critic approval source_creation_authorized must be true")
        if approval.get("production_authorized") is not False:
            errors.append("Gate A critic approval production_authorized must be false")
    else:
        if approval.get("production_authorized") is not True:
            errors.append("Gate B critic approval production_authorized must be true")
    reviewed_at = _validate_datetime(
        approval.get("reviewed_at"),
        "critic approval reviewed_at",
        errors,
    )
    if reviewed_at is not None and minimum_date is not None:
        if reviewed_at.date() < minimum_date:
            errors.append("critic approval predates the reviewed source record")


def _validate_task_id(value: object, errors: list[str]) -> None:
    if not isinstance(value, str) or not re.fullmatch(r"task-\d{4,}", value.strip()):
        errors.append("task_id must use task-NNNN format")


def _validate_date(value: object, field: str, errors: list[str]) -> date | None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{field} is required")
        return None
    try:
        parsed = date.fromisoformat(value.strip())
    except ValueError:
        errors.append(f"{field} must use YYYY-MM-DD")
        return None
    if parsed > date.today():
        errors.append(f"{field} cannot be in the future")
    return parsed


def _validate_datetime(
    value: object,
    field: str,
    errors: list[str],
) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{field} is required")
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{field} must be an ISO-8601 timestamp")
        return None
    if parsed.tzinfo is None:
        errors.append(f"{field} must include a timezone")
        return None
    if parsed.astimezone(timezone.utc) > datetime.now(timezone.utc):
        errors.append(f"{field} cannot be in the future")
    return parsed


def _validate_https_url(value: object, field: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{field} is required")
        return
    parsed = urlparse(value.strip())
    if parsed.scheme != "https" or not parsed.netloc:
        errors.append(f"{field} must be an HTTPS URL")


def _validate_reference(
    root: Path,
    value: object,
    field: str,
    errors: list[str],
) -> None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{field} is required")
        return
    parsed = urlparse(value.strip())
    if parsed.scheme or parsed.netloc:
        _validate_https_url(value, field, errors)
        return
    _repo_file(root, value, field, errors)


def _validate_rights(value: object, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append("rights must be an object")
        return
    for field in RIGHT_FIELDS:
        if value.get(field) != "PASS":
            errors.append(f"rights.{field} must be PASS")


def _validate_input_clearance(value: object, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append("input_clearance must be an object")
        return
    if value.get("project_owned_or_cleared_inputs") is not True:
        errors.append("input_clearance.project_owned_or_cleared_inputs must be true")
    for field in PROHIBITED_INPUT_FIELDS:
        if value.get(field) is not False:
            errors.append(f"input_clearance.{field} must be false")


def _validate_evidence_paths(
    root: Path,
    value: object,
    field: str,
    errors: list[str],
) -> None:
    if not isinstance(value, list) or not value:
        errors.append(f"{field} must include at least one repository evidence path")
        return
    for index, item in enumerate(value):
        _repo_file(root, item, f"{field}[{index}]", errors)


def _repo_file(root: Path, value: object, field: str, errors: list[str]) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{field} is required")
        return None
    raw = Path(value.strip())
    if raw.is_absolute() or ".." in raw.parts:
        errors.append(f"{field} must be a repository-relative path")
        return None
    target = (root / raw).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError:
        errors.append(f"{field} must stay inside the repository")
        return None
    if not target.is_file():
        errors.append(f"{field} does not exist: {raw.as_posix()}")
        return None
    return target


def _require_text(
    data: dict,
    field: str,
    errors: list[str],
    *,
    prefix: str = "",
) -> None:
    value = data.get(field)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{prefix}{field} is required")


def _write_gate_receipt(root: Path, asset_id: str, gate: str, result: dict) -> Path:
    prefix = "asset-gate-a" if gate == "A" else "asset-gate-b"
    filename = "gate_a_check.md" if gate == "A" else "gate_b_check.md"
    receipt_dir = root / "runs" / f"{prefix}-{asset_id}"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    receipt = receipt_dir / filename
    outcome = "PASS" if result["passed"] else "FAIL"
    decision = (
        "- Source creation/download is authorized; 3D production still requires Gate B."
        if gate == "A" and result["passed"]
        else "- 3D generation, cleanup, Unity copy/import, and acceptance are authorized."
        if gate == "B" and result["passed"]
        else "- `asset_factory` remains blocked for this gate."
    )
    lines = [
        f"# Asset Gate {gate} Check",
        "",
        f"Asset ID: {asset_id}",
        f"Checked: {now_iso()}",
        f"Manifest: {result['manifest'].relative_to(root).as_posix()}",
        f"Manifest SHA-256: {result['manifest_sha256'] or 'unavailable'}",
        f"Result: **{outcome}**",
        "",
        "## Findings",
        "",
    ]
    lines.extend(
        (f"- {error}" for error in result["errors"])
        if result["errors"]
        else ["- All gate requirements and the bound critic approval passed."]
    )
    lines.extend(["", "## Production Decision", "", decision, ""])
    receipt.write_text("\n".join(lines), encoding="utf-8")
    return receipt


def _result(
    asset_id: str,
    gate: str,
    source_path: str,
    manifest: Path,
    data: dict | None,
    errors: list[str],
) -> dict:
    return {
        "passed": not errors,
        "asset_id": asset_id,
        "gate": gate,
        "source_path": source_path,
        "manifest": manifest,
        "manifest_sha256": (
            sha256_gate_manifest(manifest) if manifest.is_file() else ""
        ),
        "data": data or {},
        "errors": errors,
    }


def _blocked_message(
    gate: str,
    asset_id: str,
    result: dict,
    receipt: Path,
    root: Path,
) -> str:
    summary = "; ".join(result["errors"][:3])
    return (
        f"{gate} blocked for {asset_id}: {summary}. "
        f"See {receipt.relative_to(root).as_posix()}"
    )


def _require_tracked_asset(root: Path, asset_id: str) -> None:
    index = root / "asset_pipeline" / "index.json"
    if not index.exists():
        raise CompanyError(f"asset_pipeline/index.json missing; unknown asset: {asset_id}")
    data = _read_json_object(index, "Asset index")
    if not any(item.get("id") == asset_id for item in data.get("assets", [])):
        raise CompanyError(f"Unknown asset: {asset_id}")


def _index_gate_status(root: Path, asset_id: str, gate: str) -> str:
    index = root / "asset_pipeline" / "index.json"
    if not index.exists():
        return ""
    try:
        data = json.loads(index.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ""
    if not isinstance(data, dict):
        return ""
    target = next((item for item in data.get("assets", []) if item.get("id") == asset_id), {})
    return str(target.get(f"{gate}_gate_status") or "")


def _update_gate_index(
    root: Path,
    asset_id: str,
    *,
    gate: str,
    gate_status: str,
    manifest: Path,
    receipt: Path | None,
    errors: list[str],
    allow_create: bool,
) -> None:
    index = root / "asset_pipeline" / "index.json"
    data = {"assets": []}
    if index.exists():
        data = _read_json_object(index, "Asset index")
    assets = data.setdefault("assets", [])
    target = next((item for item in assets if item.get("id") == asset_id), None)
    if target is None:
        if not allow_create:
            raise CompanyError(f"Unknown asset: {asset_id}")
        target = {"id": asset_id, "status": "briefed", "created_at": now_iso()}
        assets.append(target)
    target.update(
        {
            f"{gate}_gate_required": True,
            f"{gate}_gate_status": gate_status,
            f"{gate}_gate_manifest": manifest.relative_to(root).as_posix(),
            "updated_at": now_iso(),
        }
    )
    if receipt is not None:
        target[f"{gate}_gate_receipt"] = receipt.relative_to(root).as_posix()
    error_key = f"{gate}_gate_errors"
    if errors:
        target[error_key] = errors
    else:
        target.pop(error_key, None)
    index.parent.mkdir(parents=True, exist_ok=True)
    _write_json(index, data)


def _read_json_object(path: Path, label: str) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CompanyError(f"{label} is unreadable: {exc}") from exc
    if not isinstance(data, dict):
        raise CompanyError(f"{label} top level must be a JSON object")
    return data


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
