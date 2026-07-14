import importlib.util
import json
from pathlib import Path

from agent_tools.finals_rebuild.math_boundary_pilot import _execute_generate


def _runner_module():
    path = Path(__file__).parents[2] / "scripts" / "run_ab2d_minimal_smoke.py"
    spec = importlib.util.spec_from_file_location("ab2d_minimal_smoke_runner", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_candidate_execution_timeout_and_incremental_jsonl(tmp_path):
    runner = _runner_module()
    success = "def generate(level=1, **kwargs):\n return {'question_text':'q','correct_answer':{},'oracle_payload':{}}\n"
    status, value, error = _execute_generate(success, timeout=0.5)
    assert (status, error) == ("passed", None)
    assert value["question_text"] == "q"

    output = tmp_path / "results.jsonl"
    runner.append_jsonl_record(output, {"task_id": "first", "outcome": status})

    infinite = "def generate(level=1, **kwargs):\n while True: pass\n"
    timeout_status, timeout_value, timeout_error = _execute_generate(infinite, timeout=0.1)
    assert timeout_status == "runtime_failure"
    assert timeout_value is None and "execution_timeout" in timeout_error
    runner.append_jsonl_record(output, {"task_id": "second", "outcome": timeout_status})

    # communicate() completes after terminate/kill, so a later wrapper can run
    # without inheriting a stuck candidate child.
    assert _execute_generate(success, timeout=0.5)[0] == "passed"
    rows = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert rows == [{"outcome": "passed", "task_id": "first"}, {"outcome": "runtime_failure", "task_id": "second"}]
