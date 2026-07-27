#!/usr/bin/env python3
"""One-shot harmless sandbox smoke using formal build_bubblewrap_command.

Never loads 130-cell journals, never imports EvalPlus correctness, never uses
--execute. Safe verification helper for the /tmp/stage2-work mount fix.
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile
import time

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from scripts.diagnose_cumulative_h1_h4_modified_final_failures_v2 import (  # noqa: E402
    SANDBOX_WORK_DIR,
    build_bubblewrap_command,
)

WORKER = pathlib.Path(__file__).with_name("diagnose_v2_sandbox_smoke_worker_harmless.py")


def _read_live_cgroup_limits(command: list[str]) -> dict[str, str]:
    """Start a short-lived sandbox and read MemoryMax/TasksMax/CPUQuota from host."""
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    deadline = time.time() + 10
    worker_pid = None
    try:
        while time.time() < deadline and worker_pid is None:
            time.sleep(0.2)
            for status in pathlib.Path("/proc").glob("*/status"):
                try:
                    text = status.read_text(encoding="utf-8")
                except OSError:
                    continue
                if "Name:\tpython" not in text and "Name:\tpython3" not in text:
                    continue
                pid = status.parent.name
                try:
                    cmd = (
                        (pathlib.Path("/proc") / pid / "cmdline")
                        .read_bytes()
                        .replace(b"\x00", b" ")
                        .decode("utf-8", "replace")
                    )
                except OSError:
                    continue
                if f"{SANDBOX_WORK_DIR}/worker.py" in cmd:
                    worker_pid = pid
                    break
        if worker_pid is None:
            raise RuntimeError("live sandbox worker pid not found")
        cgroup = (pathlib.Path("/proc") / worker_pid / "cgroup").read_text(encoding="utf-8")
        rel = cgroup.strip().split(":")[-1].lstrip("/")
        base = pathlib.Path("/sys/fs/cgroup") / rel
        return {
            "worker_pid": worker_pid,
            "cgroup": rel,
            "memory_max": (base / "memory.max").read_text(encoding="utf-8").strip(),
            "memory_swap_max": (base / "memory.swap.max").read_text(encoding="utf-8").strip()
            if (base / "memory.swap.max").is_file()
            else "missing",
            "pids_max": (base / "pids.max").read_text(encoding="utf-8").strip(),
            "cpu_max": (base / "cpu.max").read_text(encoding="utf-8").strip(),
        }
    finally:
        proc.kill()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.terminate()


def main() -> int:
    if SANDBOX_WORK_DIR != "/tmp/stage2-work":
        print("unexpected SANDBOX_WORK_DIR", SANDBOX_WORK_DIR)
        return 1
    with tempfile.TemporaryDirectory(prefix="stage2_sandbox_smoke_") as temp_dir:
        host = pathlib.Path(temp_dir)
        worker = host / "worker.py"
        request = host / "request.json"
        sleep_request = host / "sleep_request.json"
        worker.write_text(WORKER.read_text(encoding="utf-8"), encoding="utf-8")
        request.write_text(json.dumps({"mode": "harmless_sandbox_smoke"}), encoding="utf-8")
        sleep_request.write_text(
            json.dumps({"mode": "harmless_sandbox_sleep", "sleep_seconds": 12}),
            encoding="utf-8",
        )
        command = build_bubblewrap_command(
            python_executable=sys.executable,
            worker_path=str(worker),
            request_path=str(request),
        )
        sleep_command = build_bubblewrap_command(
            python_executable=sys.executable,
            worker_path=str(worker),
            request_path=str(sleep_request),
        )
        joined = " ".join(command)
        if "--tmpfs /work" in joined or "/work/worker.py" in joined:
            print("FAIL command still references root /work")
            return 2
        for required in ("CPUQuota=100%", "MemoryMax=512M", "MemorySwapMax=0", "TasksMax=64"):
            if required not in joined:
                print("FAIL missing systemd property", required)
                return 2

        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
            check=False,
        )
        print("RETURNCODE", completed.returncode)
        print("STDOUT", completed.stdout)
        print("STDERR", completed.stderr)
        if completed.returncode != 0:
            return 3
        lines = [line for line in completed.stdout.splitlines() if line.strip()]
        if len(lines) != 1:
            print("FAIL expected exactly one JSON result line")
            return 4
        payload = json.loads(lines[0])

        limits = _read_live_cgroup_limits(sleep_command)
        print("LIVE_CGROUP_LIMITS", json.dumps(limits, sort_keys=True))

        checks = {
            "sandbox_started": payload.get("ok") is True and completed.returncode == 0,
            "network_isolated": payload.get("network_blocked") is True,
            "host_root_not_writable": payload.get("host_root_writable") is False,
            "work_tmpfs_writable": payload.get("work_writable") is True,
            "NoNewPrivs": payload.get("NoNewPrivs") == "1",
            "CapEff": payload.get("CapEff") in {"0000000000000000", "0"},
            "pids_limit_effective_behavior": payload.get("pids_limit_effective") is True,
            "memory_max_512MiB_host": limits.get("memory_max") == "536870912",
            "memory_swap_max_zero_host": limits.get("memory_swap_max") in {"0", "0\n"},
            "pids_max_64_host": limits.get("pids_max") == "64",
            "cpu_quota_100pct_host": limits.get("cpu_max") == "100000 100000",
            "cwd_is_work": payload.get("cwd") == SANDBOX_WORK_DIR,
            "no_root_work_mount": "--tmpfs /work" not in joined,
        }
        print("CHECKS", json.dumps(checks, indent=2, sort_keys=True))
        failed = [name for name, ok in checks.items() if not ok]
        if failed:
            print("FAILED", failed)
            return 5
        print("SMOKE_ALL_PASS")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
