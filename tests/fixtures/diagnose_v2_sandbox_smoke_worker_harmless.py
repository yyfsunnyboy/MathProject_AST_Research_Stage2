#!/usr/bin/env python3
"""Harmless fixed sandbox smoke worker for the 130-cell diagnosis runner.

This file never imports EvalPlus, never reads a candidate journal, and never
executes a candidate program. It only inspects the sandbox environment and
emits one JSON line on stdout.

MemoryMax/CPUQuota are verified by the parent smoke driver against the live
host cgroup (inside the namespace /proc/self/cgroup is remapped to 0::/).
"""

from __future__ import annotations

import json
import os
import pathlib
import socket
import sys
import time


WORK_DIR = "/tmp/stage2-work"


def _status_field(name: str) -> str:
    for line in pathlib.Path("/proc/self/status").read_text(encoding="utf-8").splitlines():
        if line.startswith(name + ":"):
            return line.split(":", 1)[1].strip()
    raise RuntimeError(f"missing /proc/self/status field {name}")


def _probe_pids_limit(target: int = 80) -> dict[str, object]:
    """Try to create many child processes; TasksMax=64 should stop this early."""
    children: list[int] = []
    hit_limit = False
    err = ""
    try:
        while len(children) < target:
            pid = os.fork()
            if pid == 0:
                time.sleep(2)
                os._exit(0)
            children.append(pid)
    except OSError as exc:
        hit_limit = True
        err = f"{type(exc).__name__}:{exc.errno}"
    for pid in children:
        try:
            os.waitpid(pid, 0)
        except ChildProcessError:
            pass
    return {
        "fork_attempts_succeeded": len(children),
        "fork_hit_limit": hit_limit,
        "fork_error": err,
        "pids_limit_effective": hit_limit and len(children) < target and len(children) <= 63,
    }


def main() -> int:
    request_path = pathlib.Path(sys.argv[1])
    request = json.loads(request_path.read_text(encoding="utf-8"))
    mode = request.get("mode")
    if mode == "harmless_sandbox_sleep":
        # Parent host-cgroup probe holds this alive briefly.
        time.sleep(float(request.get("sleep_seconds", 8)))
        print(json.dumps({"ok": True, "mode": mode}, sort_keys=True), flush=True)
        return 0
    if mode != "harmless_sandbox_smoke":
        raise SystemExit("refusing unexpected request mode")

    cwd = pathlib.Path.cwd().as_posix()
    work_probe = pathlib.Path("smoke_write_probe.txt")
    work_probe.write_text("ok\n", encoding="utf-8")
    work_writable = work_probe.is_file() and work_probe.read_text(encoding="utf-8") == "ok\n"

    host_root_writable = False
    try:
        pathlib.Path("/stage2_host_root_write_probe").write_text("no\n", encoding="utf-8")
        host_root_writable = True
    except OSError:
        host_root_writable = False

    try:
        socket.create_connection(("1.1.1.1", 53), timeout=1.0).close()
        network_blocked = False
    except OSError:
        network_blocked = True

    payload = {
        "ok": True,
        "cwd": cwd,
        "request_path": request_path.as_posix(),
        "work_dir_expected": WORK_DIR,
        "work_writable": work_writable,
        "host_root_writable": host_root_writable,
        "network_blocked": network_blocked,
        "NoNewPrivs": _status_field("NoNewPrivs"),
        "CapEff": _status_field("CapEff"),
        "pid": os.getpid(),
        "argv": list(sys.argv),
        **_probe_pids_limit(),
    }
    print(json.dumps(payload, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
