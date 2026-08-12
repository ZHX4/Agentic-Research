"""Restricted Docker execution for scientific experiments."""
from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import re
import subprocess
import time
from pathlib import Path

from agentic_research.schemas.phase7 import ArtifactRecord, ExperimentSpec, SeedRun


class SandboxViolation(RuntimeError):
    pass


class DockerSandboxExecutor:
    """Execute an ExperimentSpec in a restricted Docker container."""

    def __init__(self, docker_binary: str = "docker") -> None:
        self.docker_binary = docker_binary

    def _validate_command(self, command: list[str]) -> None:
        if not command or any(not isinstance(token, str) or not token for token in command):
            raise SandboxViolation("Command must be a non-empty argv list")
        forbidden = {"--privileged", "--network=host", "--pid=host", "--ipc=host", "-v", "--volume"}
        if any(token in forbidden for token in command):
            raise SandboxViolation("Docker mount/privilege flags are forbidden inside experiment argv")

    def _image_digest(self, image: str) -> str:
        completed = subprocess.run(
            [self.docker_binary, "image", "inspect", image, "--format", "{{json .RepoDigests}}"],
            capture_output=True,
            text=True,
            check=True,
        )
        return hashlib.sha256(completed.stdout.encode("utf-8")).hexdigest()

    @staticmethod
    def _safe_name(value: str) -> str:
        return re.sub(r"[^A-Za-z0-9._-]+", "_", value)[:80] or "dataset"

    def execute_seed(self, spec: ExperimentSpec, *, seed: int, code_dir: Path, artifact_dir: Path) -> SeedRun:
        self._validate_command(spec.command)
        if seed not in spec.seeds:
            raise ValueError(f"Seed {seed} is not declared by the experiment spec")
        if not code_dir.is_dir():
            raise FileNotFoundError(code_dir)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        self._image_digest(spec.sandbox.image)
        command = [self.docker_binary, "run", "--rm"]
        if spec.sandbox.read_only_root:
            command.append("--read-only")
        if not spec.sandbox.network_enabled:
            command += ["--network", "none"]
        command += [
            "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges:true",
            "--pids-limit", str(spec.sandbox.pids_limit),
            "--memory", f"{spec.sandbox.memory_mb}m",
            "--cpus", str(spec.sandbox.cpu_count),
            "--tmpfs", "/tmp:rw,noexec,nosuid,size=512m",
            "-v", f"{code_dir.resolve()}:{spec.sandbox.workdir}:ro",
            "-v", f"{artifact_dir.resolve()}:/outputs:rw",
            "-w", spec.sandbox.workdir,
        ]
        dataset_root = artifact_dir.parent / f"seed-{seed}-datasets"
        for dataset in spec.datasets:
            if not dataset.local_path:
                continue
            dataset_path = Path(dataset.local_path).resolve()
            if not dataset_path.exists():
                raise SandboxViolation(f"Dataset path does not exist: {dataset.local_path}")
            dataset_root.mkdir(parents=True, exist_ok=True)
            mount_target = f"/datasets/{self._safe_name(dataset.dataset_id)}"
            command += ["-v", f"{dataset_path}:{mount_target}:ro"]
        if spec.sandbox.allow_gpu:
            command += ["--gpus", "all"]
        for key in spec.sandbox.allowed_env:
            if key in os.environ:
                command += ["-e", f"{key}={os.environ[key]}"]
        command += [
            "-e", f"AGENTIC_RESEARCH_SEED={seed}",
            "-e", "AGENTIC_RESEARCH_OUTPUT_DIR=/outputs",
            "-e", "AGENTIC_RESEARCH_DATASET_ROOT=/datasets",
            spec.sandbox.image,
            *spec.command,
        ]
        started = time.monotonic()
        status = "failed"
        exit_code: int | None = None
        stdout = b""
        stderr = b""
        error: str | None = None
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                timeout=spec.sandbox.timeout_seconds,
                check=False,
            )
            stdout, stderr = completed.stdout, completed.stderr
            exit_code = completed.returncode
            status = "succeeded" if exit_code == 0 else "failed"
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout or b""
            stderr = exc.stderr or b""
            status = "timeout"
            error = f"Execution exceeded {spec.sandbox.timeout_seconds} seconds"
        except FileNotFoundError as exc:
            status = "rejected"
            error = f"Docker executable unavailable: {exc}"
        except subprocess.SubprocessError as exc:
            status = "failed"
            error = str(exc)
        duration = time.monotonic() - started
        (artifact_dir / f"seed-{seed}.stdout").write_bytes(stdout)
        (artifact_dir / f"seed-{seed}.stderr").write_bytes(stderr)
        artifacts = _collect_artifacts(artifact_dir)
        return SeedRun(
            seed=seed,
            status=status,
            exit_code=exit_code,
            duration_seconds=duration,
            artifacts=artifacts,
            stdout_sha256=hashlib.sha256(stdout).hexdigest(),
            stderr_sha256=hashlib.sha256(stderr).hexdigest(),
            error=error,
        )

    def execute(self, spec: ExperimentSpec, *, code_dir: Path, output_dir: Path) -> list[SeedRun]:
        output_dir.mkdir(parents=True, exist_ok=True)
        results: list[SeedRun] = []
        for seed in spec.seeds:
            seed_dir = output_dir / f"seed-{seed}"
            run = self.execute_seed(spec, seed=seed, code_dir=code_dir, artifact_dir=seed_dir)
            results.append(run)
            if run.status == "rejected":
                break
        return results


def _collect_artifacts(root: Path) -> list[ArtifactRecord]:
    records: list[ArtifactRecord] = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        payload = path.read_bytes()
        relative = path.relative_to(root).as_posix()
        records.append(
            ArtifactRecord(
                artifact_id="artifact:" + hashlib.sha256(relative.encode("utf-8")).hexdigest()[:20],
                relative_path=relative,
                sha256=hashlib.sha256(payload).hexdigest(),
                byte_size=len(payload),
                media_type=mimetypes.guess_type(path.name)[0] or "application/octet-stream",
            )
        )
    return records


def environment_fingerprint(spec: ExperimentSpec, image_digest: str) -> str:
    payload = json.dumps(
        {
            "image": spec.sandbox.image,
            "image_digest": image_digest,
            "network_enabled": spec.sandbox.network_enabled,
            "read_only_root": spec.sandbox.read_only_root,
            "memory_mb": spec.sandbox.memory_mb,
            "cpu_count": spec.sandbox.cpu_count,
            "pids_limit": spec.sandbox.pids_limit,
        },
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
