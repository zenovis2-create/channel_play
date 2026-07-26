"""Image-to-3D-to-Blender asset pipeline wiring."""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
from pathlib import Path

from .asset_gate import (
    approved_gate_b_source,
    asset_gate_a_init,
    evaluate_asset_gate_a,
    evaluate_asset_gate_b,
)
from .errors import CompanyError
from .timeutil import now_iso

VALID_PROVIDERS = {"rodin25", "pixal3d", "trellis2", "tripo", "both", "local"}
GENERATE_PROVIDERS = {"auto", "rodin25", "pixal3d", "trellis2", "tripo", "both", "local"}
GDX1_TRELLIS2_IMAGE = "channel-play/trellis2:gb10"
GDX1_TRELLIS2_REPO = "/home/daehan/.openclaw/repos/TRELLIS.2"
GDX1_TRELLIS2_JOBS = "/home/daehan/channel_play_image3d"
GDX1_DINOV3_MODEL = "facebook/dinov3-vitl16-pretrain-lvd1689m"
GDX1_PIXAL3D_IMAGE = "channel-play/pixal3d:gb10"
GDX1_PIXAL3D_REPO = "/home/daehan/.openclaw/repos/Pixal3D"
GDX1_PIXAL3D_DINO_MODEL = "camenduru/dinov3-vitl16-pretrain-lvd1689m"


def image3d_new(root: Path, asset_id: str, *, provider: str = "pixal3d", prompt: str = "", source_image: str = "") -> Path:
    clean = _clean_asset_id(asset_id)
    chosen_provider = (provider or "pixal3d").strip().lower()
    if chosen_provider not in VALID_PROVIDERS:
        raise CompanyError(f"Invalid image3d provider: {provider}")
    asset_gate_a_init(root, clean)
    gate_a_passed = evaluate_asset_gate_a(root, clean)["passed"]
    gate_b_result = evaluate_asset_gate_b(root, clean)
    approved_provider = (
        gate_b_result["data"].get("production", {}).get("approved_3d_provider")
        if gate_b_result["passed"]
        else None
    )
    gate_b_passed = gate_b_result["passed"] and chosen_provider == approved_provider
    production_status = (
        "waiting_for_generation"
        if gate_b_passed
        else "blocked_by_gate_b"
        if gate_a_passed
        else "blocked_by_gate_a"
    )

    description = prompt.strip() or _default_prompt(clean)
    base = root / "asset_pipeline" / "image_to_blender" / clean
    folders = {
        "concept": base / "concept",
        "source": base / "source",
        "providers": base / "providers",
        "blender": base / "blender",
        "unity": base / "unity",
    }
    for folder in folders.values():
        folder.mkdir(parents=True, exist_ok=True)

    job = {
        "schema": "channel_play.image_to_blender.v1",
        "asset_id": clean,
        "provider": chosen_provider,
        "status": (
            "image_to_blender_ready"
            if gate_b_passed
            else "waiting_for_gate_b"
            if gate_a_passed
            else "waiting_for_gate_a"
        ),
        "created_at": now_iso(),
        "prompt": description,
        "source_image": source_image.strip(),
        "installed_tools": {
            "blender": "/opt/homebrew/bin/blender",
            "tripo_blender_plugin": "/Users/daehan/.openclaw/repos/tripo-3d-for-blender",
            "trellis2": "/Users/daehan/.openclaw/repos/TRELLIS.2",
            "python_venv": ".venv/asset-forge",
        },
        "pipeline": [
            {
                "stage": "concept_image",
                "tool": "gpt_image",
                "status": "waiting_for_image" if gate_a_passed else "blocked_by_gate_a",
            },
            {
                "stage": "image_to_3d",
                "tool": chosen_provider,
                "status": production_status,
            },
            {
                "stage": "blender_cleanup",
                "tool": "blender",
                "status": "waiting_for_glb_or_fbx" if gate_b_passed else production_status,
            },
            {
                "stage": "unity_import",
                "tool": "unity",
                "status": "waiting_for_clean_asset" if gate_b_passed else production_status,
            },
            {
                "stage": "scene_binding",
                "tool": "world_builder",
                "status": "waiting_for_prefab" if gate_b_passed else production_status,
            },
        ],
        "outputs": {
            "gpt_image_prompt": f"asset_pipeline/image_to_blender/{clean}/concept/gpt_image_prompt.md",
            "source_requirements": f"asset_pipeline/image_to_blender/{clean}/source/source_image_requirements.md",
            "trellis2_job": f"asset_pipeline/image_to_blender/{clean}/providers/trellis2_job.md",
            "tripo_job": f"asset_pipeline/image_to_blender/{clean}/providers/tripo_job.md",
            "blender_cleanup_plan": f"asset_pipeline/image_to_blender/{clean}/blender/cleanup_plan.md",
            "blender_job_config": f"asset_pipeline/image_to_blender/{clean}/blender/blender_job_config.json",
            "unity_import_plan": f"asset_pipeline/image_to_blender/{clean}/unity/unity_import_plan.md",
        },
    }

    (base / "image3d_job.json").write_text(json.dumps(job, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (folders["concept"] / "gpt_image_prompt.md").write_text(
        _gpt_image_prompt(clean, description, gate_a_passed),
        encoding="utf-8",
    )
    (folders["source"] / "source_image_requirements.md").write_text(
        _source_requirements(clean, source_image, gate_a_passed),
        encoding="utf-8",
    )
    (folders["providers"] / "trellis2_job.md").write_text(
        _trellis2_job(clean, description, production_status),
        encoding="utf-8",
    )
    (folders["providers"] / "tripo_job.md").write_text(
        _tripo_job(clean, description, production_status),
        encoding="utf-8",
    )
    (folders["blender"] / "cleanup_plan.md").write_text(
        _blender_plan(clean, production_status),
        encoding="utf-8",
    )
    (folders["blender"] / "blender_job_config.json").write_text(
        json.dumps(
            _blender_config(clean, production_status),
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (folders["unity"] / "unity_import_plan.md").write_text(
        _unity_plan(clean, production_status),
        encoding="utf-8",
    )

    receipt_dir = root / "runs" / f"image-to-blender-{clean}"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    receipt = receipt_dir / "image_to_blender_receipt.md"
    receipt.write_text(
        _receipt(
            root,
            clean,
            chosen_provider,
            base,
            gate_a_passed=gate_a_passed,
            gate_b_passed=gate_b_passed,
        ),
        encoding="utf-8",
    )
    _update_asset_index(
        root,
        clean,
        chosen_provider,
        description,
        base,
        receipt,
        gate_a_passed=gate_a_passed,
        gate_b_passed=gate_b_passed,
    )
    return receipt


def image3d_state(root: Path) -> dict:
    base = root / "asset_pipeline" / "image_to_blender"
    jobs = []
    if base.exists():
        for path in sorted(base.glob("*/image3d_job.json"), key=lambda item: item.stat().st_mtime, reverse=True):
            try:
                job = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            job["path"] = path.relative_to(root).as_posix()
            jobs.append(job)
    return {"status": "ready" if jobs else "empty", "jobCount": len(jobs), "jobs": jobs[:16]}


def image3d_generate(root: Path, asset_id: str, *, provider: str = "auto", timeout: int = 1800) -> Path:
    clean = _clean_asset_id(asset_id)
    chosen_provider = (provider or "auto").strip().lower()
    if chosen_provider not in GENERATE_PROVIDERS:
        raise CompanyError(f"Invalid image3d generation provider: {provider}")
    approved_source = approved_gate_b_source(root, clean, provider=chosen_provider)

    base = root / "asset_pipeline" / "image_to_blender" / clean
    job_path = base / "image3d_job.json"
    if not job_path.exists():
        raise CompanyError(f"image3d job not found. Run: tools/channelctl asset image3d {clean} --provider both")

    job = json.loads(job_path.read_text(encoding="utf-8"))
    source_image = _resolve_source_image(root, base, job)
    if source_image is None or not source_image.is_file():
        raise CompanyError(
            f"Gate B source is not available for {clean}: "
            f"{approved_source.relative_to(root).as_posix()}"
        )
    if source_image.resolve() != approved_source:
        raise CompanyError(
            "image3d job source_image does not match the exact file approved by Gate B"
        )

    run_dir = root / "runs" / f"image-to-blender-{clean}"
    run_dir.mkdir(parents=True, exist_ok=True)
    provider_dir = base / "providers"
    provider_dir.mkdir(parents=True, exist_ok=True)

    checks = {
        "rodin25_api_key": bool(_rodin25_key()),
        "tripo_api_key": bool(_tripo_key()),
        "source_image": source_image.relative_to(root).as_posix() if source_image and source_image.exists() else "",
        "gdx1": _gdx1_status(),
    }

    generated_model: Path | None = None
    external_attempts: list[dict] = []
    selected = _provider_order(chosen_provider, job.get("provider", "trellis2"))

    for item in selected:
        if item == "rodin25":
            result = _try_rodin25_generate(root, clean, source_image, timeout, job.get("prompt", ""))
            external_attempts.append(result)
            if result.get("status") == "generated" and result.get("model"):
                generated_model = root / result["model"]
                break
        elif item == "pixal3d":
            result = _try_pixal3d_generate_or_prepare(root, clean, source_image, timeout)
            external_attempts.append(result)
            if result.get("status") == "generated" and result.get("model"):
                generated_model = root / result["model"]
                break
        elif item == "tripo":
            result = _try_tripo_generate(root, clean, source_image, timeout)
            external_attempts.append(result)
            if result.get("status") == "generated" and result.get("model"):
                generated_model = root / result["model"]
                break
        elif item == "trellis2":
            result = _try_trellis2_generate_or_prepare(root, clean, source_image, timeout)
            external_attempts.append(result)
            if result.get("status") == "generated" and result.get("model"):
                generated_model = root / result["model"]
                break

    if generated_model is None and chosen_provider == "local":
        local_result = _generate_local_blender_model(root, clean, job)
        external_attempts.append(local_result)
        generated_model = root / local_result["model"]
        if not checks["source_image"] and local_result.get("source_image"):
            checks["source_image"] = local_result["source_image"]
    elif generated_model is None:
        reasons = "; ".join(
            str(attempt.get("reason") or attempt.get("status") or "unknown failure")
            for attempt in external_attempts
        )
        raise CompanyError(
            f"Gate B approved provider {chosen_provider}, but it did not produce a model"
            f"{': ' + reasons if reasons else ''}; unreviewed local fallback is prohibited"
        )

    cleanup_receipt = _run_blender_cleanup(root, clean, generated_model)
    unity_ready = _unity_ready_model(root, clean)
    unity_asset = _copy_unity_asset(root, clean, unity_ready)

    job["status"] = "model_generated"
    job["updated_at"] = now_iso()
    job["source_image"] = checks["source_image"]
    job.setdefault("generated_outputs", {})
    job["generated_outputs"].update(
        {
            "selected_model": generated_model.relative_to(root).as_posix(),
            "unity_ready_model": unity_ready.relative_to(root).as_posix(),
            "unity_asset_model": unity_asset.relative_to(root).as_posix(),
            "cleanup_receipt": cleanup_receipt.relative_to(root).as_posix(),
            "model_generation_receipt": f"runs/image-to-blender-{clean}/model_generation_receipt.md",
        }
    )
    for stage in job.get("pipeline", []):
        if stage.get("stage") == "concept_image":
            stage["status"] = "source_available" if checks["source_image"] else "local_preview_generated"
        if stage.get("stage") == "image_to_3d":
            stage["status"] = "generated"
        if stage.get("stage") == "blender_cleanup":
            stage["status"] = "cleaned"
        if stage.get("stage") == "unity_import":
            stage["status"] = "unity_ready_glb"
    job_path.write_text(json.dumps(job, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    _update_generated_asset_index(root, clean, generated_model, unity_ready)
    receipt = run_dir / "model_generation_receipt.md"
    receipt.write_text(
        _generation_receipt(root, clean, chosen_provider, checks, external_attempts, generated_model, unity_ready, unity_asset, cleanup_receipt),
        encoding="utf-8",
    )
    return receipt


def _clean_asset_id(asset_id: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9_-]+", "_", asset_id.strip()).strip("_").lower()
    if not clean:
        raise CompanyError("asset id required")
    return clean


def _provider_order(requested: str, job_provider: str) -> list[str]:
    if requested == "local":
        return []
    if requested == "auto":
        provider = (job_provider or "trellis2").lower()
        if provider == "both":
            return ["rodin25", "pixal3d", "tripo", "trellis2"]
        if provider in {"rodin25", "pixal3d", "tripo", "trellis2"}:
            return [provider]
        return ["rodin25", "pixal3d", "tripo", "trellis2"]
    if requested == "both":
        return ["rodin25", "pixal3d", "tripo", "trellis2"]
    return [requested]


def _resolve_source_image(root: Path, base: Path, job: dict) -> Path | None:
    candidates: list[Path] = []
    source_text = (job.get("source_image") or "").strip()
    if source_text:
        source_path = Path(source_text)
        candidates.append(source_path if source_path.is_absolute() else root / source_path)
    candidates.append(base / "source" / "concept.png")
    candidates.append(base / "source" / "concept.jpg")
    candidates.append(base / "source" / "concept.jpeg")
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _tripo_key() -> str:
    return os.environ.get("TRIPO_API_KEY") or os.environ.get("TRIPO3D_API_KEY") or ""


def _rodin25_key() -> str:
    return os.environ.get("HYPER3D_API_KEY") or os.environ.get("RODIN_API_KEY") or ""


def _try_rodin25_generate(root: Path, asset_id: str, source_image: Path | None, timeout: int, prompt: str = "") -> dict:
    output_dir = root / "asset_pipeline" / "image_to_blender" / asset_id / "providers" / "rodin25_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    dry_run = os.environ.get("CHANNEL_PLAY_RODIN25_DRY_RUN", "").lower() in {"1", "true", "yes"}
    if not _rodin25_key() and not dry_run:
        return {"provider": "rodin25", "status": "skipped", "reason": "HYPER3D_API_KEY or RODIN_API_KEY is not set"}
    if (source_image is None or not source_image.exists()) and not prompt.strip():
        return {"provider": "rodin25", "status": "skipped", "reason": "source image and prompt are both missing"}

    runner = root / "tools" / "asset_forge" / "rodin25_image_to_model.py"
    python = root / ".venv" / "asset-forge" / "bin" / "python"
    if not python.exists():
        python = Path(shutil.which("python3") or "python3")
    command = [
        str(python),
        str(runner),
        "--output-dir",
        str(output_dir),
        "--timeout",
        str(timeout),
        "--tier",
        os.environ.get("CHANNEL_PLAY_RODIN25_TIER", "Gen-2.5-Medium"),
        "--material",
        os.environ.get("CHANNEL_PLAY_RODIN25_MATERIAL", "PBR"),
        "--geometry-format",
        os.environ.get("CHANNEL_PLAY_RODIN25_FORMAT", "glb"),
    ]
    if source_image and source_image.exists():
        command.extend(["--image", str(source_image)])
    if prompt.strip():
        command.extend(["--prompt", prompt.strip()])
    quality_override = os.environ.get("CHANNEL_PLAY_RODIN25_QUALITY_OVERRIDE", "")
    if quality_override:
        command.extend(["--quality-override", quality_override])
    if dry_run:
        command.append("--dry-run")
    proc = subprocess.run(command, cwd=root, text=True, capture_output=True, check=False, timeout=timeout + 120)
    (output_dir / "rodin25_stdout.log").write_text(proc.stdout, encoding="utf-8")
    (output_dir / "rodin25_stderr.log").write_text(proc.stderr, encoding="utf-8")
    if proc.returncode != 0:
        return {"provider": "rodin25", "status": "failed", "reason": proc.stderr.strip()[-500:] or proc.stdout.strip()[-500:]}
    receipt_path = output_dir / "rodin25_receipt.json"
    if not receipt_path.exists():
        return {"provider": "rodin25", "status": "failed", "reason": "Rodin Gen-2.5 receipt missing"}
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if dry_run:
        return {"provider": "rodin25", "status": "dry_run_ok", "receipt": receipt_path.relative_to(root).as_posix()}
    model = receipt.get("selected_model")
    return {"provider": "rodin25", "status": "generated", "model": Path(model).relative_to(root).as_posix() if model else "", "receipt": receipt_path.relative_to(root).as_posix()}


def _try_pixal3d_generate_or_prepare(root: Path, asset_id: str, source_image: Path | None, timeout: int) -> dict:
    output_dir = root / "asset_pipeline" / "image_to_blender" / asset_id / "providers" / "pixal3d_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    gdx1_attempt = _try_gdx1_pixal3d_generate(root, asset_id, source_image, timeout)
    if gdx1_attempt.get("status") == "generated":
        return gdx1_attempt

    status = _gdx1_pixal3d_status()
    reason = gdx1_attempt.get("reason") or "gdx1 Pixal3D generation did not produce a GLB"
    receipt = {
        "provider": "pixal3d",
        "status": "not_ready",
        "updated_at": now_iso(),
        "gdx1": status,
        "gdx1_docker_attempt": gdx1_attempt,
        "source_image": str(source_image) if source_image else "",
        "required_next": [
            "Clone TencentARC/Pixal3D into /home/daehan/.openclaw/repos/Pixal3D on gdx1.",
            "Build Docker image channel-play/pixal3d:gb10 from tools/asset_forge/gdx1_pixal3d_runtime/Dockerfile.channel_play.",
            "Re-run tools/channelctl asset generate3d <asset-id> --provider pixal3d.",
        ],
    }
    if status.get("pixal3d_repo") == "yes":
        receipt["required_next"].pop(0)
    if status.get("pixal3d_image") == "yes":
        receipt["required_next"] = [item for item in receipt["required_next"] if "Build Docker image" not in item]
    (output_dir / "pixal3d_readiness.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "provider": "pixal3d",
        "status": "not_ready",
        "reason": reason,
        "receipt": (output_dir / "pixal3d_readiness.json").relative_to(root).as_posix(),
    }


def _try_gdx1_pixal3d_generate(root: Path, asset_id: str, source_image: Path | None, timeout: int) -> dict:
    output_dir = root / "asset_pipeline" / "image_to_blender" / asset_id / "providers" / "pixal3d_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    if os.environ.get("CHANNEL_PLAY_PIXAL3D_DISABLE_GDX1", "").lower() in {"1", "true", "yes"}:
        return {"provider": "pixal3d_gdx1", "status": "skipped", "reason": "CHANNEL_PLAY_PIXAL3D_DISABLE_GDX1 is set"}
    if source_image is None or not source_image.exists():
        return {"provider": "pixal3d_gdx1", "status": "skipped", "reason": "source image missing"}

    image_name = os.environ.get("CHANNEL_PLAY_PIXAL3D_IMAGE", GDX1_PIXAL3D_IMAGE)
    remote_dir = f"{GDX1_TRELLIS2_JOBS}/{asset_id}_pixal3d"
    remote_output = f"{remote_dir}/output"
    remote_input = f"{remote_dir}/concept{source_image.suffix.lower()}"
    remote_script = f"{remote_dir}/run_image_to_glb.py"
    local_script = root / "tools" / "asset_forge" / "gdx1_pixal3d_runtime" / "run_image_to_glb.py"
    if not local_script.exists():
        return {"provider": "pixal3d_gdx1", "status": "failed", "reason": f"runner missing: {local_script.relative_to(root)}"}

    dry_run = os.environ.get("CHANNEL_PLAY_PIXAL3D_DRY_RUN", "").lower() in {"1", "true", "yes"}
    status = _gdx1_pixal3d_status()
    if status.get("pixal3d_repo") != "yes":
        return {"provider": "pixal3d_gdx1", "status": "not_ready", "reason": "gdx1 Pixal3D repo missing at /home/daehan/.openclaw/repos/Pixal3D"}
    if status.get("pixal3d_image") != "yes":
        return {"provider": "pixal3d_gdx1", "status": "not_ready", "reason": f"gdx1 Docker image missing: {image_name}"}
    if not dry_run and status.get("camenduru_dinov3") != "yes":
        return {"provider": "pixal3d_gdx1", "status": "not_ready", "reason": "gdx1 cannot access camenduru DINOv3 dependency for Pixal3D"}

    mkdir_cmd = f"mkdir -p {shlex.quote(remote_output)}"
    prep = subprocess.run(["ssh", "gdx1", mkdir_cmd], cwd=root, text=True, capture_output=True, check=False, timeout=30)
    if prep.returncode != 0:
        return {"provider": "pixal3d_gdx1", "status": "failed", "reason": prep.stderr.strip()[-500:] or "failed to create remote Pixal3D job dir"}

    input_copy = subprocess.run(
        ["scp", str(source_image), f"gdx1:{remote_input}"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
        timeout=60,
    )
    if input_copy.returncode != 0:
        return {"provider": "pixal3d_gdx1", "status": "failed", "reason": input_copy.stderr.strip()[-500:] or "failed to copy source image to gdx1"}
    script_copy = subprocess.run(
        ["scp", str(local_script), f"gdx1:{remote_script}"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
        timeout=60,
    )
    if script_copy.returncode != 0:
        return {"provider": "pixal3d_gdx1", "status": "failed", "reason": script_copy.stderr.strip()[-500:] or "failed to copy Pixal3D runner to gdx1"}

    runner_args = [
        "python",
        "/workspace/channel_play_job/run_image_to_glb.py",
        "--asset-id",
        asset_id,
        "--image",
        f"/workspace/channel_play_job/{Path(remote_input).name}",
        "--output-dir",
        "/workspace/channel_play_job/output",
        "--resolution",
        os.environ.get("CHANNEL_PLAY_PIXAL3D_RESOLUTION", "1024"),
    ]
    if os.environ.get("CHANNEL_PLAY_PIXAL3D_LOW_VRAM", "1").lower() in {"1", "true", "yes"}:
        runner_args.append("--low-vram")
    if dry_run:
        runner_args.append("--dry-run")

    pixal3d_env_args: list[str] = []
    for env_name in (
        "CHANNEL_PLAY_PIXAL3D_SKIP_REMBG",
        "CHANNEL_PLAY_PIXAL3D_ALPHA_THRESHOLD",
        "CHANNEL_PLAY_PIXAL3D_MANUAL_FOV",
        "CHANNEL_PLAY_NATTEN_FNA_BACKEND",
    ):
        env_value = os.environ.get(env_name)
        if env_value:
            pixal3d_env_args.extend(["-e", f"{env_name}={env_value}"])

    docker_cmd = [
        "sudo",
        "docker",
        "run",
        "--rm",
        "--gpus",
        "all",
        "--ipc=host",
        "-w",
        "/workspace/Pixal3D",
        "--ulimit",
        "memlock=-1",
        "--ulimit",
        "stack=67108864",
        "-e",
        "HF_TOKEN",
        "-e",
        "HUGGING_FACE_HUB_TOKEN",
        "-e",
        "PYTORCH_ALLOC_CONF=expandable_segments:True",
        "-e",
        "ATTN_BACKEND=sdpa",
        "-e",
        "PYTHONPATH=/workspace/Pixal3D:/workspace/TRELLIS.2",
        *pixal3d_env_args,
        "-v",
        f"{GDX1_PIXAL3D_REPO}:/workspace/Pixal3D",
        "-v",
        f"{GDX1_TRELLIS2_REPO}:/workspace/TRELLIS.2",
        "-v",
        f"{remote_dir}:/workspace/channel_play_job",
        "-v",
        "/home/daehan/.cache/huggingface:/root/.cache/huggingface",
        image_name,
        *runner_args,
    ]
    remote_command = (
        f"sudo docker image inspect {shlex.quote(image_name)} >/dev/null 2>&1 && "
        + " ".join(shlex.quote(part) for part in docker_cmd)
    )
    proc = subprocess.run(["ssh", "gdx1", remote_command], cwd=root, text=True, capture_output=True, check=False, timeout=timeout + 120)
    (output_dir / "pixal3d_gdx1_stdout.log").write_text(proc.stdout, encoding="utf-8")
    (output_dir / "pixal3d_gdx1_stderr.log").write_text(proc.stderr, encoding="utf-8")

    copy_back = subprocess.run(
        ["scp", "-r", f"gdx1:{remote_output}/.", str(output_dir)],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
        timeout=120,
    )
    receipt_path = output_dir / "pixal3d_gdx1_receipt.json"
    models = sorted(output_dir.glob("*.glb"), key=lambda item: item.stat().st_mtime, reverse=True)
    receipt: dict = {}
    if receipt_path.exists():
        try:
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            receipt = {}
    if proc.returncode != 0:
        reason = proc.stderr.strip()[-900:] or proc.stdout.strip()[-900:] or "gdx1 Pixal3D Docker command failed"
        if receipt:
            reason = receipt.get("error") or receipt.get("status") or reason
        return {"provider": "pixal3d_gdx1", "status": "failed", "reason": reason, "receipt": receipt_path.relative_to(root).as_posix() if receipt_path.exists() else ""}
    if dry_run and receipt.get("status") == "dry_run_ok":
        return {"provider": "pixal3d_gdx1", "status": "dry_run_ok", "reason": "gdx1 Pixal3D Docker runtime imports and dependency checks passed", "receipt": receipt_path.relative_to(root).as_posix()}
    if copy_back.returncode != 0:
        return {"provider": "pixal3d_gdx1", "status": "failed", "reason": copy_back.stderr.strip()[-500:] or "failed to copy gdx1 Pixal3D output back to local workspace", "receipt": receipt_path.relative_to(root).as_posix() if receipt_path.exists() else ""}
    if not models:
        return {"provider": "pixal3d_gdx1", "status": "failed", "reason": "gdx1 Pixal3D completed but no GLB was copied back", "receipt": receipt_path.relative_to(root).as_posix() if receipt_path.exists() else ""}
    return {"provider": "pixal3d_gdx1", "status": "generated", "model": models[0].relative_to(root).as_posix(), "receipt": receipt_path.relative_to(root).as_posix() if receipt_path.exists() else ""}


def _try_tripo_generate(root: Path, asset_id: str, source_image: Path | None, timeout: int) -> dict:
    output_dir = root / "asset_pipeline" / "image_to_blender" / asset_id / "providers" / "tripo_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    key = _tripo_key()
    if not key:
        return {"provider": "tripo", "status": "skipped", "reason": "TRIPO_API_KEY or TRIPO3D_API_KEY is not set"}
    if source_image is None or not source_image.exists():
        return {"provider": "tripo", "status": "skipped", "reason": "source image missing"}

    runner = root / "tools" / "asset_forge" / "tripo_image_to_model.py"
    python = root / ".venv" / "asset-forge" / "bin" / "python"
    if not python.exists():
        python = Path(shutil.which("python3") or "python3")
    command = [
        str(python),
        str(runner),
        "--image",
        str(source_image),
        "--output-dir",
        str(output_dir),
        "--timeout",
        str(timeout),
    ]
    proc = subprocess.run(command, cwd=root, text=True, capture_output=True, check=False, timeout=timeout + 120)
    (output_dir / "tripo_stdout.log").write_text(proc.stdout, encoding="utf-8")
    (output_dir / "tripo_stderr.log").write_text(proc.stderr, encoding="utf-8")
    if proc.returncode != 0:
        return {"provider": "tripo", "status": "failed", "reason": proc.stderr.strip()[-500:] or proc.stdout.strip()[-500:]}
    receipt_path = output_dir / "tripo_receipt.json"
    if not receipt_path.exists():
        return {"provider": "tripo", "status": "failed", "reason": "tripo receipt missing"}
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    model = receipt.get("selected_model")
    return {"provider": "tripo", "status": "generated", "model": Path(model).relative_to(root).as_posix() if model else "", "receipt": receipt_path.relative_to(root).as_posix()}


def _try_trellis2_generate_or_prepare(root: Path, asset_id: str, source_image: Path | None, timeout: int) -> dict:
    output_dir = root / "asset_pipeline" / "image_to_blender" / asset_id / "providers" / "trellis2_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    gdx1_attempt = _try_gdx1_trellis2_generate(root, asset_id, source_image, timeout)
    if gdx1_attempt.get("status") == "generated":
        return gdx1_attempt

    space_attempt = {"provider": "trellis2_space", "status": "skipped", "reason": "gdx1 runtime attempted first"}
    if os.environ.get("CHANNEL_PLAY_TRELLIS2_SKIP_HF_SPACE", "1").lower() not in {"1", "true", "yes"}:
        space_attempt = _try_trellis2_space(root, asset_id, source_image, timeout)
        if space_attempt.get("status") == "generated":
            return space_attempt

    status = _gdx1_status()
    attempt_reason = str(gdx1_attempt.get("reason") or "")
    required_next = [
        "Free enough gdx1 GPU memory for TRELLIS.2-4B inference.",
        "Keep Docker image channel-play/trellis2:gb10 available on gdx1.",
        "Re-run tools/channelctl asset generate3d <asset-id> --provider trellis2.",
    ]
    lower_reason = attempt_reason.lower()
    if "lacks gated repo approval" in lower_reason or "requires approval" in lower_reason:
        required_next.insert(0, "Request/accept access for facebook/dinov3-vitl16-pretrain-lvd1689m with the Hugging Face account currently logged in on gdx1.")
        required_next.insert(1, "Verify gated access: ssh daehan@100.78.48.61 '/home/daehan/.local/bin/hf download facebook/dinov3-vitl16-pretrain-lvd1689m config.json --local-dir /tmp/hf-dinov3-auth-check'.")
    elif "gated repo" in lower_reason or "gated facebook/dinov3" in lower_reason:
        required_next.insert(0, "Request/accept access for facebook/dinov3-vitl16-pretrain-lvd1689m on the Hugging Face account used by gdx1.")
        required_next.insert(1, "Authenticate gdx1 with an approved Hugging Face read token: /home/daehan/.local/bin/hf auth login --force.")
    receipt = {
        "provider": "trellis2",
        "status": "not_ready",
        "updated_at": now_iso(),
        "gdx1": status,
        "gdx1_docker_attempt": gdx1_attempt,
        "hf_space_attempt": space_attempt,
        "source_image": str(source_image) if source_image else "",
        "required_next": required_next,
    }
    if source_image and source_image.exists():
        remote_input = f"~/channel_play_image3d/{asset_id}/concept{source_image.suffix.lower()}"
        receipt["remote_input_target"] = remote_input
        subprocess.run(["ssh", "gdx1", f"mkdir -p ~/channel_play_image3d/{asset_id}"], cwd=root, check=False)
        subprocess.run(["scp", str(source_image), f"gdx1:{remote_input}"], cwd=root, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    (output_dir / "trellis2_readiness.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    reason = gdx1_attempt.get("reason") or "gdx1 TRELLIS.2 Docker generation did not produce a GLB"
    if space_attempt.get("status") == "failed" and space_attempt.get("reason"):
        reason = f"{reason}; HF Space: {space_attempt['reason']}"
    return {"provider": "trellis2", "status": "not_ready", "reason": reason, "receipt": (output_dir / "trellis2_readiness.json").relative_to(root).as_posix()}

def _try_gdx1_trellis2_generate(root: Path, asset_id: str, source_image: Path | None, timeout: int) -> dict:
    output_dir = root / "asset_pipeline" / "image_to_blender" / asset_id / "providers" / "trellis2_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    if os.environ.get("CHANNEL_PLAY_TRELLIS2_DISABLE_GDX1", "").lower() in {"1", "true", "yes"}:
        return {"provider": "trellis2_gdx1", "status": "skipped", "reason": "CHANNEL_PLAY_TRELLIS2_DISABLE_GDX1 is set"}
    if source_image is None or not source_image.exists():
        return {"provider": "trellis2_gdx1", "status": "skipped", "reason": "source image missing"}

    image_name = os.environ.get("CHANNEL_PLAY_TRELLIS2_IMAGE", GDX1_TRELLIS2_IMAGE)
    remote_dir = f"{GDX1_TRELLIS2_JOBS}/{asset_id}"
    remote_output = f"{remote_dir}/output"
    remote_input = f"{remote_dir}/concept{source_image.suffix.lower()}"
    remote_script = f"{remote_dir}/run_image_to_glb.py"
    local_script = root / "tools" / "asset_forge" / "gdx1_trellis2_runtime" / "run_image_to_glb.py"
    if not local_script.exists():
        return {"provider": "trellis2_gdx1", "status": "failed", "reason": f"runner missing: {local_script.relative_to(root)}"}
    dry_run = os.environ.get("CHANNEL_PLAY_TRELLIS2_DRY_RUN", "").lower() in {"1", "true", "yes"}
    if not dry_run:
        status = _gdx1_status()
        if status.get("hf_token") != "yes":
            return {
                "provider": "trellis2_gdx1",
                "status": "not_ready",
                "reason": "gdx1 Hugging Face token missing; run /home/daehan/.local/bin/hf auth login --force with an approved token for gated facebook/dinov3 dependencies",
            }
        dinov3_access = _gdx1_dinov3_access()
        if dinov3_access.get("status") != "ok":
            return {
                "provider": "trellis2_gdx1",
                "status": "not_ready",
                "reason": dinov3_access.get("reason", "gdx1 DINOv3 gated repo access check failed"),
                "gated_access": dinov3_access,
            }

    mkdir_cmd = f"mkdir -p {shlex.quote(remote_output)}"
    prep = subprocess.run(["ssh", "gdx1", mkdir_cmd], cwd=root, text=True, capture_output=True, check=False, timeout=30)
    if prep.returncode != 0:
        return {"provider": "trellis2_gdx1", "status": "failed", "reason": prep.stderr.strip()[-500:] or "failed to create remote job dir"}
    input_copy = subprocess.run(
        ["scp", str(source_image), f"gdx1:{remote_input}"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
        timeout=60,
    )
    if input_copy.returncode != 0:
        return {
            "provider": "trellis2_gdx1",
            "status": "failed",
            "reason": input_copy.stderr.strip()[-500:] or "failed to copy source image to gdx1",
        }
    script_copy = subprocess.run(
        ["scp", str(local_script), f"gdx1:{remote_script}"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
        timeout=60,
    )
    if script_copy.returncode != 0:
        return {
            "provider": "trellis2_gdx1",
            "status": "failed",
            "reason": script_copy.stderr.strip()[-500:] or "failed to copy TRELLIS.2 runner to gdx1",
        }

    runner_args = [
        "python",
        "/workspace/channel_play_job/run_image_to_glb.py",
        "--asset-id",
        asset_id,
        "--image",
        f"/workspace/channel_play_job/{Path(remote_input).name}",
        "--output-dir",
        "/workspace/channel_play_job/output",
        "--model",
        os.environ.get("CHANNEL_PLAY_TRELLIS2_MODEL", "microsoft/TRELLIS.2-4B"),
        "--pipeline-type",
        os.environ.get("CHANNEL_PLAY_TRELLIS2_PIPELINE_TYPE", "512"),
        "--seed",
        os.environ.get("CHANNEL_PLAY_TRELLIS2_SEED", "42"),
        "--decimation-target",
        os.environ.get("CHANNEL_PLAY_TRELLIS2_DECIMATION_TARGET", "500000"),
        "--texture-size",
        os.environ.get("CHANNEL_PLAY_TRELLIS2_TEXTURE_SIZE", "2048"),
        "--max-num-tokens",
        os.environ.get("CHANNEL_PLAY_TRELLIS2_MAX_NUM_TOKENS", "24576"),
    ]
    if dry_run:
        runner_args.append("--dry-run")

    docker_cmd = [
        "sudo",
        "docker",
        "run",
        "--rm",
        "--gpus",
        "all",
        "--ipc=host",
        "-w",
        "/workspace/TRELLIS.2",
        "--ulimit",
        "memlock=-1",
        "--ulimit",
        "stack=67108864",
        "-e",
        "HF_TOKEN",
        "-e",
        "HUGGING_FACE_HUB_TOKEN",
        "-e",
        "PYTORCH_ALLOC_CONF=expandable_segments:True",
        "-e",
        "PYTHONPATH=/workspace/TRELLIS.2",
        "-v",
        f"{GDX1_TRELLIS2_REPO}:/workspace/TRELLIS.2",
        "-v",
        f"{remote_dir}:/workspace/channel_play_job",
        "-v",
        "/home/daehan/.cache/huggingface:/root/.cache/huggingface",
        image_name,
        *runner_args,
    ]
    remote_command = (
        f"sudo docker image inspect {shlex.quote(image_name)} >/dev/null 2>&1 && "
        + " ".join(shlex.quote(part) for part in docker_cmd)
    )
    proc = subprocess.run(["ssh", "gdx1", remote_command], cwd=root, text=True, capture_output=True, check=False, timeout=timeout + 120)
    (output_dir / "trellis2_gdx1_stdout.log").write_text(proc.stdout, encoding="utf-8")
    (output_dir / "trellis2_gdx1_stderr.log").write_text(proc.stderr, encoding="utf-8")

    copy_back = subprocess.run(
        ["scp", "-r", f"gdx1:{remote_output}/.", str(output_dir)],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
        timeout=120,
    )
    receipt_path = output_dir / "trellis2_gdx1_receipt.json"
    models = sorted(output_dir.glob("*.glb"), key=lambda item: item.stat().st_mtime, reverse=True)
    receipt: dict = {}
    if receipt_path.exists():
        try:
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            receipt = {}
    if proc.returncode != 0:
        reason = proc.stderr.strip()[-900:] or proc.stdout.strip()[-900:] or "gdx1 TRELLIS.2 Docker command failed"
        if receipt:
            reason = receipt.get("error") or receipt.get("status") or reason
        return {
            "provider": "trellis2_gdx1",
            "status": "failed",
            "reason": reason,
            "receipt": receipt_path.relative_to(root).as_posix() if receipt_path.exists() else "",
        }
    if dry_run and receipt.get("status") == "dry_run_ok":
        return {
            "provider": "trellis2_gdx1",
            "status": "dry_run_ok",
            "reason": "gdx1 TRELLIS.2 Docker runtime imports and CUDA checks passed",
            "receipt": receipt_path.relative_to(root).as_posix(),
        }
    if copy_back.returncode != 0:
        return {
            "provider": "trellis2_gdx1",
            "status": "failed",
            "reason": copy_back.stderr.strip()[-500:] or "failed to copy gdx1 TRELLIS.2 output back to local workspace",
            "receipt": receipt_path.relative_to(root).as_posix() if receipt_path.exists() else "",
        }
    if not models:
        return {
            "provider": "trellis2_gdx1",
            "status": "failed",
            "reason": "gdx1 TRELLIS.2 completed but no GLB was copied back",
            "receipt": receipt_path.relative_to(root).as_posix() if receipt_path.exists() else "",
        }
    return {
        "provider": "trellis2_gdx1",
        "status": "generated",
        "model": models[0].relative_to(root).as_posix(),
        "receipt": receipt_path.relative_to(root).as_posix() if receipt_path.exists() else "",
    }


def _try_trellis2_space(root: Path, asset_id: str, source_image: Path | None, timeout: int) -> dict:
    output_dir = root / "asset_pipeline" / "image_to_blender" / asset_id / "providers" / "trellis2_space_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    if source_image is None or not source_image.exists():
        return {"provider": "trellis2_space", "status": "skipped", "reason": "source image missing"}
    runner = root / "tools" / "asset_forge" / "hf_trellis2_space_image_to_model.py"
    python = root / ".venv" / "asset-forge" / "bin" / "python"
    if not python.exists():
        python = Path(shutil.which("python3") or "python3")
    command = [
        str(python),
        str(runner),
        "--image",
        str(source_image),
        "--output-dir",
        str(output_dir),
        "--timeout",
        str(timeout),
    ]
    proc = subprocess.run(command, cwd=root, text=True, capture_output=True, check=False, timeout=timeout + 120)
    (output_dir / "trellis2_space_stdout.log").write_text(proc.stdout, encoding="utf-8")
    (output_dir / "trellis2_space_stderr.log").write_text(proc.stderr, encoding="utf-8")
    receipt_path = output_dir / "trellis2_space_receipt.json"
    if proc.returncode != 0:
        reason = proc.stderr.strip()[-700:] or proc.stdout.strip()[-700:] or "trellis2 space failed"
        if receipt_path.exists():
            try:
                receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
                reason = receipt.get("reason") or reason
            except json.JSONDecodeError:
                pass
        return {"provider": "trellis2_space", "status": "failed", "reason": reason, "receipt": receipt_path.relative_to(root).as_posix() if receipt_path.exists() else ""}
    if not receipt_path.exists():
        return {"provider": "trellis2_space", "status": "failed", "reason": "trellis2 space receipt missing"}
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    model = receipt.get("selected_model")
    if not model:
        return {"provider": "trellis2_space", "status": "failed", "reason": "trellis2 space did not return a model", "receipt": receipt_path.relative_to(root).as_posix()}
    return {"provider": "trellis2_space", "status": "generated", "model": Path(model).relative_to(root).as_posix(), "receipt": receipt_path.relative_to(root).as_posix()}


def _gdx1_status() -> dict:
    image_name = os.environ.get("CHANNEL_PLAY_TRELLIS2_IMAGE", GDX1_TRELLIS2_IMAGE)
    command = (
        "echo ssh=ok; "
        "command -v nvidia-smi >/dev/null 2>&1 && echo nvidia_smi=yes || echo nvidia_smi=no; "
        "test -d ~/.openclaw/repos/TRELLIS.2 && echo trellis2_repo=yes || echo trellis2_repo=no; "
        "command -v docker >/dev/null 2>&1 && echo docker=yes || echo docker=no; "
        "test -x ~/.local/bin/hf && echo hf_cli=yes || echo hf_cli=no; "
        "test -s ~/.cache/huggingface/token || test -n \"$HF_TOKEN\" || test -n \"$HUGGING_FACE_HUB_TOKEN\" "
        "&& echo hf_token=yes || echo hf_token=no; "
        f"sudo docker image inspect {shlex.quote(image_name)} >/dev/null 2>&1 && echo trellis2_image=yes || echo trellis2_image=no"
    )
    try:
        proc = subprocess.run(["ssh", "gdx1", command], text=True, capture_output=True, check=False, timeout=15)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ssh": "failed", "error": str(exc)}
    data: dict[str, str | int] = {"returncode": proc.returncode}
    for line in proc.stdout.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            data[key.strip()] = value.strip()
    if proc.stderr.strip():
        data["stderr"] = proc.stderr.strip()[-500:]
    return data


def _gdx1_dinov3_access() -> dict:
    command = (
        "/home/daehan/.local/bin/hf download "
        f"{shlex.quote(GDX1_DINOV3_MODEL)} config.json "
        "--local-dir /tmp/hf-dinov3-auth-check"
    )
    try:
        proc = subprocess.run(["ssh", "gdx1", command], text=True, capture_output=True, check=False, timeout=90)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"status": "failed", "reason": f"gdx1 DINOv3 access check failed: {exc}"}
    output = "\n".join([proc.stdout.strip(), proc.stderr.strip()]).strip()
    if proc.returncode == 0:
        return {"status": "ok", "model": GDX1_DINOV3_MODEL, "config": "/tmp/hf-dinov3-auth-check/config.json"}
    reason = output[-900:] or "gdx1 DINOv3 gated repo access check failed"
    if "Access denied" in reason or "requires approval" in reason or "401" in reason:
        reason = (
            f"gdx1 HF account lacks gated repo approval for {GDX1_DINOV3_MODEL}; "
            "request/accept access on Hugging Face with the logged-in account, then rerun"
        )
    return {"status": "not_ready", "model": GDX1_DINOV3_MODEL, "reason": reason}


def _gdx1_pixal3d_status() -> dict:
    image_name = os.environ.get("CHANNEL_PLAY_PIXAL3D_IMAGE", GDX1_PIXAL3D_IMAGE)
    command = (
        "echo ssh=ok; "
        f"test -d {shlex.quote(GDX1_PIXAL3D_REPO)} && echo pixal3d_repo=yes || echo pixal3d_repo=no; "
        f"sudo docker image inspect {shlex.quote(image_name)} >/dev/null 2>&1 && echo pixal3d_image=yes || echo pixal3d_image=no; "
        "/home/daehan/.local/bin/hf download camenduru/dinov3-vitl16-pretrain-lvd1689m config.json "
        "--local-dir /tmp/hf-camenduru-dinov3-check >/dev/null 2>&1 && echo camenduru_dinov3=yes || echo camenduru_dinov3=no"
    )
    try:
        proc = subprocess.run(["ssh", "gdx1", command], text=True, capture_output=True, check=False, timeout=90)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ssh": "failed", "error": str(exc)}
    data: dict[str, str | int] = {"returncode": proc.returncode}
    for line in proc.stdout.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            data[key.strip()] = value.strip()
    if proc.stderr.strip():
        data["stderr"] = proc.stderr.strip()[-500:]
    return data


def _generate_local_blender_model(root: Path, asset_id: str, job: dict) -> dict:
    output_dir = root / "asset_pipeline" / "image_to_blender" / asset_id / "providers" / "local_blender_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    config = {
        "asset_id": asset_id,
        "prompt": job.get("prompt", ""),
        "output_dir": output_dir.relative_to(root).as_posix(),
    }
    config_path = output_dir / "local_blender_generate_config.json"
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    blender = shutil.which("blender") or "/opt/homebrew/bin/blender"
    script = root / "tools" / "asset_forge" / "blender_generate_pyramid_asset.py"
    proc = subprocess.run(
        [blender, "--background", "--python", str(script), "--", str(config_path)],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
        timeout=300,
    )
    (output_dir / "local_blender_stdout.log").write_text(proc.stdout, encoding="utf-8")
    (output_dir / "local_blender_stderr.log").write_text(proc.stderr, encoding="utf-8")
    if proc.returncode != 0:
        raise CompanyError(f"Local Blender generation failed: {(proc.stderr or proc.stdout).strip()[-800:]}")
    model = output_dir / f"{asset_id}_model.glb"
    preview = output_dir / f"{asset_id}_preview.png"
    if not model.exists():
        raise CompanyError(f"Local Blender generation did not create {model}")
    return {
        "provider": "local_blender",
        "status": "generated",
        "model": model.relative_to(root).as_posix(),
        "preview": preview.relative_to(root).as_posix(),
        "receipt": (output_dir / "local_blender_receipt.json").relative_to(root).as_posix(),
    }


def _run_blender_cleanup(root: Path, asset_id: str, generated_model: Path) -> Path:
    config_path = root / "asset_pipeline" / "image_to_blender" / asset_id / "blender" / "blender_job_config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["input_model"] = generated_model.relative_to(root).as_posix()
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output_dir = root / "asset_pipeline" / "unity_ready" / asset_id
    output_dir.mkdir(parents=True, exist_ok=True)
    blender = shutil.which("blender") or "/opt/homebrew/bin/blender"
    proc = subprocess.run(
        [blender, "--background", "--python", str(root / "tools" / "asset_forge" / "blender_image_to_unity_cleanup.py"), "--", str(config_path)],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
        timeout=300,
    )
    (output_dir / "blender_cleanup_stdout.log").write_text(proc.stdout, encoding="utf-8")
    (output_dir / "blender_cleanup_stderr.log").write_text(proc.stderr, encoding="utf-8")
    if proc.returncode != 0:
        raise CompanyError(f"Blender cleanup failed: {(proc.stderr or proc.stdout).strip()[-800:]}")
    receipt = output_dir / "blender_cleanup_receipt.json"
    if not receipt.exists():
        raise CompanyError("Blender cleanup receipt missing")
    return receipt


def _unity_ready_model(root: Path, asset_id: str) -> Path:
    model = root / "asset_pipeline" / "unity_ready" / asset_id / f"{asset_id}_unity_ready.glb"
    if not model.exists():
        raise CompanyError(f"Unity-ready model missing: {model}")
    return model


def _copy_unity_asset(root: Path, asset_id: str, unity_ready: Path) -> Path:
    target_dir = root / "Assets" / "_Project" / "Art" / "Maps" / asset_id
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / unity_ready.name
    shutil.copy2(unity_ready, target)
    preview = root / "asset_pipeline" / "image_to_blender" / asset_id / "providers" / "local_blender_output" / f"{asset_id}_preview.png"
    if preview.exists():
        shutil.copy2(preview, target_dir / preview.name)
    return target


def _update_generated_asset_index(root: Path, asset_id: str, generated_model: Path, unity_ready: Path) -> None:
    index = root / "asset_pipeline" / "index.json"
    data = {"assets": []}
    if index.exists():
        data = json.loads(index.read_text(encoding="utf-8"))
    assets = data.setdefault("assets", [])
    target = next((item for item in assets if item.get("id") == asset_id), None)
    if target is None:
        target = {"id": asset_id, "created_at": now_iso()}
        assets.append(target)
    target.update(
        {
            "status": "generated",
            "image_to_blender_status": "model_generated",
            "generated_model": generated_model.relative_to(root).as_posix(),
            "unity_ready_model": unity_ready.relative_to(root).as_posix(),
            "updated_at": now_iso(),
        }
    )
    index.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _generation_receipt(
    root: Path,
    asset_id: str,
    provider: str,
    checks: dict,
    attempts: list[dict],
    generated_model: Path,
    unity_ready: Path,
    unity_asset: Path,
    cleanup_receipt: Path,
) -> str:
    lines = [
        "# Image To Blender Model Generation Receipt",
        "",
        f"Asset ID: {asset_id}",
        f"Requested provider: {provider}",
        f"Updated: {now_iso()}",
        "Status: model_generated",
        "",
        "## Outputs",
        f"- Selected model: `{generated_model.relative_to(root).as_posix()}`",
        f"- Unity-ready GLB: `{unity_ready.relative_to(root).as_posix()}`",
        f"- Unity asset GLB: `{unity_asset.relative_to(root).as_posix()}`",
        f"- Blender cleanup receipt: `{cleanup_receipt.relative_to(root).as_posix()}`",
        "",
        "## Runtime Checks",
        f"- Source image: `{checks.get('source_image') or 'missing'}`",
        f"- Rodin Gen-2.5 API key available: `{checks.get('rodin25_api_key')}`",
        f"- Tripo API key available: `{checks.get('tripo_api_key')}`",
        f"- gdx1: `{json.dumps(checks.get('gdx1'), ensure_ascii=False)}`",
        "",
        "## Attempts",
    ]
    for attempt in attempts:
        lines.append(f"- `{attempt.get('provider')}`: `{attempt.get('status')}` {attempt.get('reason', '')}".rstrip())
        if attempt.get("model"):
            lines.append(f"  - Model: `{attempt['model']}`")
        if attempt.get("receipt"):
            lines.append(f"  - Receipt: `{attempt['receipt']}`")
    lines.extend(
        [
            "",
            "## Interpretation",
            "- A real GLB was generated and normalized through Blender cleanup.",
            "- Rodin Gen-2.5/Pixal3D/Tripo/TRELLIS.2 are wired as execution targets, but external AI generation requires their runtime prerequisites.",
            "- Rodin Gen-2.5 uses Hyper3D API when `HYPER3D_API_KEY` or `RODIN_API_KEY` is set and outputs GLB directly.",
            "- Pixal3D uses gdx1 Docker image `channel-play/pixal3d:gb10` and outputs GLB directly when the Pixal3D repo/image are available.",
            "- TRELLIS.2 uses gdx1 Docker image `channel-play/trellis2:gb10` when a source image and GPU memory are available.",
            "",
        ]
    )
    return "\n".join(lines)


def _default_prompt(asset_id: str) -> str:
    return f"{asset_id} realistic game-ready pyramid temple asset, ancient limestone blocks, readable silhouette, clean separated parts, no text or logos"


def _gpt_image_prompt(
    asset_id: str,
    prompt: str,
    gate_a_passed: bool,
) -> str:
    return "\n".join(
        [
            f"# GPT Image Prompt: {asset_id}",
            "",
            (
                "Status: ready_for_source_creation"
                if gate_a_passed
                else "Status: blocked_by_gate_a"
            ),
            "",
            "Create a production concept image for image-to-3D conversion.",
            "",
            "## Prompt",
            prompt,
            "",
            "## Requirements",
            "- Single main object or connected environment chunk.",
            "- Clear full silhouette on plain background.",
            "- Orthographic front, side, top, and three-quarter reference if making a sheet.",
            "- For TRELLIS.2, prefer one isolated foreground object with transparent or clean background.",
            "- For Tripo, include enough visual detail but avoid baked labels and copyrighted marks.",
            "- Preserve real pyramid proportions, stepped limestone block rhythm, entrance, inner chambers, relic props.",
            "",
        ]
    )


def _source_requirements(
    asset_id: str,
    source_image: str,
    gate_a_passed: bool,
) -> str:
    return "\n".join(
        [
            "# Source Image Requirements",
            "",
            f"Asset ID: {asset_id}",
            (
                "Status: waiting_for_approved_source"
                if gate_a_passed
                else "Status: blocked_by_gate_a"
            ),
            f"Current source image: {source_image or 'not provided'}",
            "",
            "- Save input image as `source/concept.png`.",
            "- Prefer square 1024 or higher.",
            "- Keep the asset fully visible, not cropped.",
            "- Use clean background or alpha if possible.",
            "- Record source/license notes here before generation.",
            "",
        ]
    )


def _trellis2_job(
    asset_id: str,
    prompt: str,
    production_status: str,
) -> str:
    return "\n".join(
        [
            f"# TRELLIS.2 Job: {asset_id}",
            "",
            f"Status: {production_status}",
            "Runtime target: gdx1 NVIDIA GPU or cloud GPU. Mac Studio is not the preferred runtime for TRELLIS.2 inference.",
            "",
            "## Input",
            "- `source/concept.png` from GPT Image or user image.",
            "",
            "## Desired Output",
            "- GLB with texture/PBR material if available.",
            "- Keep mesh as close to source image as possible.",
            "- Export to `asset_pipeline/image_to_blender/{asset_id}/providers/trellis2_output/`.",
            "",
            "## Prompt Context",
            prompt,
            "",
        ]
    )


def _tripo_job(
    asset_id: str,
    prompt: str,
    production_status: str,
) -> str:
    return "\n".join(
        [
            f"# Tripo Job: {asset_id}",
            "",
            f"Status: {production_status}",
            "Local install: `/Users/daehan/.openclaw/repos/tripo-3d-for-blender` linked into Blender user add-ons.",
            "Python venv: `.venv/asset-forge` with `tripo3d` installed.",
            "",
            "## Input",
            "- `source/concept.png` from GPT Image or user image.",
            "",
            "## Desired Output",
            "- GLB or FBX.",
            "- Export to `asset_pipeline/image_to_blender/{asset_id}/providers/tripo_output/`.",
            "",
            "## Prompt Context",
            prompt,
            "",
        ]
    )


def _blender_plan(asset_id: str, production_status: str) -> str:
    return "\n".join(
        [
            f"# Blender Cleanup Plan: {asset_id}",
            "",
            f"Status: {production_status}",
            "",
            "Use `tools/asset_forge/blender_image_to_unity_cleanup.py` after TRELLIS.2 or Tripo produces GLB/FBX.",
            "",
            "## Cleanup Rules",
            "- Normalize scale to Unity meters.",
            "- Apply transforms.",
            "- Set origin to world/gameplay pivot.",
            "- Rename render meshes with `CP_` prefix.",
            "- Add or preserve collider proxy objects with `COL_` prefix.",
            "- Export clean GLB to `asset_pipeline/unity_ready/{asset_id}/`.",
            "",
        ]
    )


def _blender_config(asset_id: str, production_status: str) -> dict:
    return {
        "asset_id": asset_id,
        "status": production_status,
        "input_model": f"asset_pipeline/image_to_blender/{asset_id}/providers/INPUT_MODEL.glb",
        "output_dir": f"asset_pipeline/unity_ready/{asset_id}",
        "object_prefix": f"CP_{asset_id}",
        "collider_prefix": "COL_",
        "target_unit": "meter",
    }


def _unity_plan(asset_id: str, production_status: str) -> str:
    return "\n".join(
        [
            f"# Unity Import Plan: {asset_id}",
            "",
            f"Status: {production_status}",
            "",
            f"Target model folder: `Assets/_Project/Art/Maps/{asset_id}`",
            f"Target prefab folder: `Assets/_Project/Prefabs/Maps/{asset_id}`",
            "",
            "## Acceptance",
            "- Model visible in Unity scene.",
            "- Colliders or proxy colliders present.",
            "- Prefab can replace the primitive blockout chunk.",
            "- Screenshot evidence captured.",
            "- Unity play mode still runs.",
            "",
        ]
    )


def _receipt(
    root: Path,
    asset_id: str,
    provider: str,
    base: Path,
    *,
    gate_a_passed: bool,
    gate_b_passed: bool,
) -> str:
    rel_base = base.relative_to(root).as_posix()
    status = (
        "image_to_blender_ready"
        if gate_b_passed
        else "waiting_for_gate_b"
        if gate_a_passed
        else "waiting_for_gate_a"
    )
    return "\n".join(
        [
            "# Image To Blender Receipt",
            "",
            f"Asset ID: {asset_id}",
            f"Provider: {provider}",
            f"Updated: {now_iso()}",
            f"Status: {status}",
            "",
            "## Artifacts",
            f"- Job: {rel_base}/image3d_job.json",
            f"- GPT Image prompt: {rel_base}/concept/gpt_image_prompt.md",
            f"- Source requirements: {rel_base}/source/source_image_requirements.md",
            f"- TRELLIS.2 job: {rel_base}/providers/trellis2_job.md",
            f"- Tripo job: {rel_base}/providers/tripo_job.md",
            f"- Blender cleanup: {rel_base}/blender/cleanup_plan.md",
            f"- Unity import: {rel_base}/unity/unity_import_plan.md",
            "",
            "## Installed Tools",
            "- Blender: `/opt/homebrew/bin/blender`",
            "- Tripo Blender plugin: `/Users/daehan/.openclaw/repos/tripo-3d-for-blender`",
            "- TRELLIS.2 source: `/Users/daehan/.openclaw/repos/TRELLIS.2`",
            "- Python venv: `.venv/asset-forge`",
            "",
        ]
    )


def _update_asset_index(
    root: Path,
    asset_id: str,
    provider: str,
    prompt: str,
    base: Path,
    receipt: Path,
    *,
    gate_a_passed: bool,
    gate_b_passed: bool,
) -> None:
    index = root / "asset_pipeline" / "index.json"
    data = {"assets": []}
    if index.exists():
        data = json.loads(index.read_text(encoding="utf-8"))
    assets = data.setdefault("assets", [])
    target = next((item for item in assets if item.get("id") == asset_id), None)
    if target is None:
        target = {"id": asset_id, "created_at": now_iso()}
        assets.append(target)
    target.update(
        {
            "image_to_blender_status": (
                "image_to_blender_ready"
                if gate_b_passed
                else "waiting_for_gate_b"
                if gate_a_passed
                else "waiting_for_gate_a"
            ),
            "provider": provider,
            "prompt": prompt,
            "image_to_blender_job": (base / "image3d_job.json").relative_to(root).as_posix(),
            "image_to_blender_receipt": receipt.relative_to(root).as_posix(),
            "source_license": "pending_generated_or_project_owned",
            "updated_at": now_iso(),
        }
    )
    index.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
