"""
runner.py — single-job subprocess executor with a line-streamed log buffer.

Plan §3 decision 1: the pipeline runs as a SUBPROCESS with the exact argv the
CLI uses (never imported for deploys — it has sys.exit calls, module-level
config loading, and long FTP transfers). Plan §9.4 invariant 2: ONE job at a
time; PS4 state files are transaction records and concurrent writers corrupt
them (Exp 227/232/237 all trace to this class).

The runner owns the process; the SSE endpoint (server.py /api/stream) tails the
shared log buffer. Cancel terminates the whole process group.
"""

from __future__ import annotations

import os
import signal
import subprocess
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

from . import deploy, paths

MAX_BUFFER_LINES = 20000  # ring; a full deploy emits a few thousand lines


@dataclass
class Job:
    """One subprocess invocation (pipeline or helper script)."""

    id: int
    argv: list[str]
    cwd: str
    started_at: float
    pid: int | None = None
    ended_at: float | None = None
    exit_code: int | None = None
    cancelled: bool = False
    lines: list[str] = field(default_factory=list)
    lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    label: str = ""
    command_line: str = ""


class SingleJobRunner:
    """Allows ONE job at a time; queues nothing (the UI says 'busy')."""

    def __init__(self):
        self._job: Job | None = None
        self._lock = threading.Lock()
        # Flags the UI has applied but the PS4 read hasn't confirmed yet —
        # purely informational for the Flags page's pending badges.
        self.pending_flags: dict | None = None

    # -- state queries -----------------------------------------------------
    @property
    def current(self) -> Job | None:
        with self._lock:
            return self._job

    def is_busy(self) -> bool:
        job = self.current
        return job is not None and job.exit_code is None and not job.cancelled

    def status(self) -> dict:
        job = self.current
        if job is None:
            return {"running": False, "job": None}
        with job.lock:
            return {
                "running": self.is_busy(),
                "job": {
                    "id": job.id,
                    "label": job.label,
                    "command": f"python3 tools/full_custom_song_pipeline.py "
                               f"{' '.join(job.argv)}",
                    "started_at": job.started_at,
                    "ended_at": job.ended_at,
                    "exit_code": job.exit_code,
                    "cancelled": job.cancelled,
                    "line_count": len(job.lines),
                },
            }

    def lines_since(self, after_index: int = 0) -> tuple[int, list[str]]:
        """(new_index, lines) — SSE long-poll contract."""
        job = self.current
        if job is None:
            return 0, []
        with job.lock:
            new = job.lines[after_index:]
            return len(job.lines), new

    # -- job lifecycle ------------------------------------------------------
    def start(self, argv: list[str], label: str = "") -> Job:
        """Run the PIPELINE with the given argv (the thin-layer deploy path)."""
        pipeline = paths.find_pipeline()
        return self._spawn(["python3", str(pipeline), *argv],
                            label=label, command=deploy.pipeline_command(argv))

    def start_script(self, script: str, argv: list[str], label: str = "") -> Job:
        """Run a helper script (e.g. backup-beat-saber-deluxe-files.py) with
        the same single-job + streaming guarantees. Thin layer: the script is
        the authority for its own behavior; the webapp only streams output."""
        rel = script
        try:
            rel = str(Path(script).relative_to(paths.RELEASE_ROOT))
        except ValueError:
            pass
        return self._spawn(["python3", script, *argv],
                           label=label, command=f"python3 {rel} {' '.join(argv)}")

    def _spawn(self, popen_argv: list[str], label: str, command: str) -> Job:
        if self.is_busy():
            raise RuntimeError(
                "A job is already running — one at a time (PS4 state files "
                "are transaction records; concurrent writers corrupt them). "
                "Wait for it to finish or cancel it first.")
        with self._lock:
            job = Job(
                id=int(time.time()),
                argv=list(popen_argv[2:]),  # the script's own argv (after python3 + script)
                # CWD = the release/checkout root (same semantics as the
                # example scripts; the pipeline resolves the rest itself).
                cwd=str(paths.RELEASE_ROOT),
                started_at=time.time(),
                label=label,
                command_line=command,
            )
            self._job = job
        proc = subprocess.Popen(
            popen_argv,
            cwd=job.cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,          # line-buffered read
            start_new_session=True,  # own process group → cancel kills children
        )
        job.pid = proc.pid

        def _drain():
            assert proc.stdout is not None
            truncated = False
            for line in proc.stdout:
                with job.lock:
                    if len(job.lines) < MAX_BUFFER_LINES:
                        job.lines.append(line.rstrip("\n"))
                    elif not truncated:
                        job.lines.append("… log truncated (max lines reached)")
                        truncated = True
            proc.wait()
            with job.lock:
                job.exit_code = proc.returncode
                job.ended_at = time.time()
                # A finished flags job clears the pending-flags hint
                if self.pending_flags and job.exit_code is not None:
                    self.pending_flags = None

        threading.Thread(target=_drain, daemon=True).start()
        return job

    def cancel(self) -> bool:
        """Terminate the process group (lftp children die too)."""
        job = self.current
        if job is None or job.exit_code is not None:
            return False
        if job.pid:
            try:
                os.killpg(os.getpgid(job.pid), signal.SIGTERM)
            except (ProcessLookupError, PermissionError):
                pass
        with job.lock:
            job.cancelled = True
        return True
