from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).parents[2]
SCRIPT = REPO_ROOT / "scripts" / "verify_finals_rebuild.sh"


def _write_executable(path: Path, body: str) -> None:
    path.write_text("#!/usr/bin/env bash\n" + body, encoding="utf-8")
    path.chmod(0o755)


def _run(tmp_path: Path, *args: str, pytest_exit: int = 0, dirty: bool = False):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log = tmp_path / "calls.log"
    _write_executable(bin_dir / "python", f'''echo "python $@" >> "{log}"
if [[ "$1 $2 $3" == "-m pytest --version" ]]; then exit 0; fi
if [[ "$1" == "--version" ]]; then echo "Python fake"; exit 0; fi
if [[ "$1 $2" == "-m pytest" ]]; then exit {pytest_exit}; fi
exit 0
''')
    status = "echo ' M dirty.py'" if dirty else ":"
    _write_executable(bin_dir / "git", f'''echo "git $@" >> "{log}"
case "$1 $2" in
  "branch --show-current") echo main ;;
  "log -1") echo "deadbeef test" ;;
  "status --short") {status} ;;
  "diff --check") : ;;
esac
''')
    env = {**os.environ, "PATH": f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}"}
    completed = subprocess.run(["bash", str(SCRIPT), *args], cwd=REPO_ROOT, text=True,
        capture_output=True, env=env)
    return completed, log.read_text(encoding="utf-8") if log.exists() else ""


@pytest.mark.parametrize("args", [(), ("unknown",), ("targeted", "extra")])
def test_usage_errors(args, tmp_path):
    completed, calls = _run(tmp_path, *args)
    assert completed.returncode == 2
    assert "Usage: verify_finals_rebuild.sh" in completed.stderr
    assert calls == ""


@pytest.mark.parametrize(("mode", "expected"), [
    ("targeted", "test_math_dev_replay.py"),
    ("related", "test_math_validator.py"),
    ("full", "tests/finals_rebuild"),
])
def test_modes_invoke_expected_pytest_targets(mode, expected, tmp_path):
    completed, calls = _run(tmp_path, mode)
    assert completed.returncode == 0
    assert expected in calls
    assert f"VERIFICATION PASSED: {mode}" in completed.stdout


def test_related_mode_includes_generator_pilot_tests(tmp_path):
    completed, calls = _run(tmp_path, "related")
    assert completed.returncode == 0
    assert "test_generator_evaluator.py" in calls
    assert "test_generator_integration_pilot.py" in calls


def test_pytest_failure_is_propagated_without_success_banner(tmp_path):
    completed, _ = _run(tmp_path, "targeted", pytest_exit=7)
    assert completed.returncode == 7
    assert "VERIFICATION PASSED" not in completed.stdout


def test_dirty_tree_warns_and_still_runs_pytest(tmp_path):
    completed, calls = _run(tmp_path, "targeted", dirty=True)
    assert completed.returncode == 0
    assert "WARNING: working tree is dirty" in completed.stderr
    assert "python -m pytest" in calls


def test_missing_pytest_returns_environment_error(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _write_executable(bin_dir / "python", "exit 1")
    env = {**os.environ, "PATH": f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}"}
    completed = subprocess.run(["bash", str(SCRIPT), "targeted"], cwd=REPO_ROOT,
        text=True, capture_output=True, env=env)
    assert completed.returncode == 2
    assert "pytest is unavailable" in completed.stderr
