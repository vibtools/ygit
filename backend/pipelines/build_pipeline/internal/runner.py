from __future__ import annotations

import os
import shlex
import subprocess
import sys
import time
from pathlib import Path

from backend.pipelines.build_pipeline.schemas import BuildExecutionInput, BuildExecutionResult, BuildLogLine


class BuildRunner:
    """Controlled subprocess runner for worker-owned repository checkouts.

    This is intentionally not imported by API routes. It executes allowlisted
    build tools with shell=False, a sanitized environment, cwd confinement, and
    per-command timeout. Provider tokens must never be passed into this runner.
    """

    _blocked_env_fragments = (
        "SECRET",
        "TOKEN",
        "PASSWORD",
        "COOKIE",
        "SESSION",
        "PRIVATE",
        "CREDENTIAL",
    )
    _allowed_executables = {
        "npm",
        "pnpm",
        "yarn",
        "bun",
        "npx",
        "node",
        "python",
        "python3",
        Path(sys.executable).name.lower().replace(".exe", ""),
    }
    _blocked_shell_tokens = ("&&", "||", ";", "|", ">", "<", "`", "$(", "${")

    def run(self, input_data: BuildExecutionInput) -> BuildExecutionResult:
        started = time.monotonic()
        logs: list[BuildLogLine] = []

        try:
            cwd = self._resolve_working_directory(input_data)
            output_dir = self._resolve_output_directory(cwd, input_data.plan.output_directory)
            env = self._safe_environment(input_data.environment)

            commands = []
            if input_data.plan.install_command:
                commands.append(("install", input_data.plan.install_command))
            commands.append(("build", input_data.plan.build_command))

            for stage, command in commands:
                logs.append(BuildLogLine(stream="system", message=f"Running {stage}: {command}"))
                result = self._run_command(command, cwd=cwd, env=env, timeout_seconds=input_data.plan.timeout_seconds)
                logs.extend(result["logs"])
                if result["status"] != "succeeded":
                    return self._result(
                        status=result["status"],
                        started=started,
                        output_directory=output_dir,
                        logs=logs,
                        exit_code=result["exit_code"],
                        error_message=result["error_message"],
                    )

            artifact_ready = output_dir.exists() and any(output_dir.iterdir())
            return self._result(
                status="succeeded" if artifact_ready else "failed",
                started=started,
                output_directory=output_dir,
                logs=logs,
                exit_code=0,
                error_message=None if artifact_ready else "Build finished, but output directory is empty or missing.",
            )
        except ValueError as exc:
            return self._result(
                status="invalid",
                started=started,
                output_directory=Path(input_data.plan.output_directory),
                logs=logs,
                exit_code=None,
                error_message=str(exc),
            )

    def _resolve_working_directory(self, input_data: BuildExecutionInput) -> Path:
        repository_path = Path(input_data.repository_path).resolve()
        if not repository_path.exists() or not repository_path.is_dir():
            raise ValueError("Repository checkout directory does not exist.")

        root_directory = input_data.plan.root_directory.strip()
        if root_directory in {"", "/", "\\"}:
            raise ValueError("Invalid build root directory.")

        cwd = (repository_path / root_directory).resolve()
        if cwd != repository_path and repository_path not in cwd.parents:
            raise ValueError("Build root directory escapes repository checkout.")
        if not cwd.exists() or not cwd.is_dir():
            raise ValueError("Build root directory does not exist.")
        return cwd

    def _resolve_output_directory(self, cwd: Path, output_directory: str) -> Path:
        if output_directory.startswith(("/", "\\")) or ".." in Path(output_directory).parts:
            raise ValueError("Output directory must stay inside repository checkout.")

        output = (cwd / output_directory).resolve()
        if output != cwd and cwd not in output.parents:
            raise ValueError("Output directory escapes repository checkout.")
        return output

    def _safe_environment(self, requested_environment: dict[str, str]) -> dict[str, str]:
        env: dict[str, str] = {
            "CI": "true",
            "NODE_ENV": "production",
        }

        for key in ("PATH", "HOME", "USER", "USERNAME", "SYSTEMROOT", "TEMP", "TMP", "APPDATA", "LOCALAPPDATA"):
            value = os.environ.get(key)
            if value:
                env[key] = value

        for key, value in requested_environment.items():
            upper_key = key.upper()
            if any(fragment in upper_key for fragment in self._blocked_env_fragments):
                raise ValueError(f"Unsafe build environment key blocked: {key}")
            if not key.replace("_", "").isalnum():
                raise ValueError(f"Invalid build environment key: {key}")
            env[key] = str(value)

        return env

    def _parse_command(self, command: str) -> list[str]:
        if any(token in command for token in self._blocked_shell_tokens):
            raise ValueError("Build command contains unsupported shell operators.")

        args = [part.strip().strip('"').strip("'") for part in shlex.split(command, posix=False)]
        args = [part for part in args if part]
        if not args:
            raise ValueError("Build command is empty.")

        executable = Path(args[0]).name.lower().replace(".exe", "")
        if executable not in self._allowed_executables:
            raise ValueError(f"Build executable is not allowlisted: {Path(args[0]).name}")

        return args

    def _run_command(
        self,
        command: str,
        *,
        cwd: Path,
        env: dict[str, str],
        timeout_seconds: int,
    ) -> dict[str, object]:
        args = self._parse_command(command)

        try:
            completed = subprocess.run(
                args,
                cwd=str(cwd),
                env=env,
                shell=False,
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            logs = self._logs_from_output(exc.stdout or "", exc.stderr or "")
            return {
                "status": "timed_out",
                "exit_code": None,
                "logs": logs,
                "error_message": "Build command timed out.",
            }

        logs = self._logs_from_output(completed.stdout, completed.stderr)
        return {
            "status": "succeeded" if completed.returncode == 0 else "failed",
            "exit_code": completed.returncode,
            "logs": logs,
            "error_message": None if completed.returncode == 0 else "Build command failed.",
        }

    def _logs_from_output(self, stdout: str, stderr: str) -> list[BuildLogLine]:
        logs: list[BuildLogLine] = []
        for stream, output in (("stdout", stdout), ("stderr", stderr)):
            for line in output.splitlines()[:200]:
                clean = line.strip()
                if clean:
                    logs.append(BuildLogLine(stream=stream, message=clean[:500]))
        return logs

    def _result(
        self,
        *,
        status: str,
        started: float,
        output_directory: Path,
        logs: list[BuildLogLine],
        exit_code: int | None,
        error_message: str | None,
    ) -> BuildExecutionResult:
        duration_ms = int((time.monotonic() - started) * 1000)
        artifact_ready = output_directory.exists() and output_directory.is_dir() and any(output_directory.iterdir())
        return BuildExecutionResult(
            status=status,
            exit_code=exit_code,
            duration_ms=duration_ms,
            output_directory=str(output_directory),
            artifact_ready=artifact_ready,
            logs=logs,
            error_message=error_message,
        )
