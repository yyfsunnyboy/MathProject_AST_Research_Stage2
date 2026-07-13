import json
import tempfile
from pathlib import Path

from agent_tools.finals_rebuild.math_boundary_pilot import CONDITIONS, TASK_IDS, _execute_generate, build_ab1_prompt, build_ab2g_prompt, classify_response, frozen_payloads, load_pilot_tasks, main, run_pilot

MANIFEST = Path(__file__).parent / "fixtures" / "math_generation_tasks_ce115_pilot.jsonl"


def test_frozen_pilot_is_five_tasks_by_three_repeats():
    tasks = load_pilot_tasks(MANIFEST)
    assert tuple(task["task_id"] for task in tasks) == TASK_IDS
    assert len(frozen_payloads(tasks)) == 15


def test_classification_passes_and_detects_schema_failure():
    task = load_pilot_tasks(MANIFEST)[0]
    frozen = frozen_payloads((task,), (2026071301,))[0]
    payload = json.dumps(frozen["oracle_payload"], sort_keys=True)
    source = "def generate(level=1, **kwargs):\n return {'question_text':'q','correct_answer':{'quotient_coefficients':[1, 1],'remainder':0},'oracle_payload':" + payload + "}\n"
    assert classify_response(source, frozen, task)[0] in {"passed", "answer_incorrect"}
    assert classify_response("def generate(): pass", frozen, task)[0] == "schema_failure"


def test_polynomial_ab1_prompt_requires_canonical_answer_schema():
    task = load_pilot_tasks(MANIFEST)[0]
    frozen = frozen_payloads((task,), (2026071301,))[0]
    prompt = build_ab1_prompt(task, frozen)
    assert "quotient_coefficients" in prompt and "remainder" in prompt
    assert "JSON-compatible dict" in prompt
    assert "[3, -1]" not in prompt and '"remainder": 0' not in prompt
    assert json.dumps(frozen["oracle_payload"], sort_keys=True) in prompt


def test_non_polynomial_ab1_prompts_require_canonical_answer_schemas():
    tasks = {task["oracle_type"]: task for task in load_pilot_tasks(MANIFEST)}
    cases = {
        "rpm_circumference_kph": (2026071301, ("coefficient", "unit", "1 rpm")),
        "largest_proper_divisor_logic": (2026071301, ("claims", "boolean list", "frozen claims order")),
        "alternating_sequence_threshold": (2026071301, ("specified_session_laps", "first_exceed_week", "first_exceed_day")),
    }
    for oracle_type, (seed, keys) in cases.items():
        task = tasks[oracle_type]
        frozen = frozen_payloads((task,), (seed,))[0]
        prompt = build_ab1_prompt(task, frozen)
        assert all(key in prompt for key in keys)
        assert "JSON-compatible dict" in prompt
        assert json.dumps(frozen["oracle_payload"], sort_keys=True) in prompt


def test_mock_run_writes_required_artifacts():
    tasks = load_pilot_tasks(MANIFEST)
    def client(url, payload, timeout):
        return {"message": {"content": "def generate(level=1, **kwargs):\n return {}"}, "prompt_eval_count": 1, "eval_count": 2}
    with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
        summary = run_pilot(tasks, output_root=directory, run_id="pilot", repeat_seeds=(1, 2, 3), client=client)
        assert summary["total_cells"] == 30
        assert {path.name for path in (Path(directory) / "pilot").iterdir()} >= {"manifest.json", "frozen_payloads.jsonl", "cell_results.jsonl", "summary.json", "failure_examples.jsonl"}


def test_ab2g_prompt_preserves_ab1_prompt_unchanged_as_a_prefix():
    task = load_pilot_tasks(MANIFEST)[0]
    frozen = frozen_payloads((task,), (2026071301,))[0]
    ab1_prompt = build_ab1_prompt(task, frozen)
    ab2g_prompt = build_ab2g_prompt(task, frozen)
    assert ab2g_prompt.startswith(ab1_prompt)
    assert "quotient_coefficients" in ab2g_prompt and "remainder" in ab2g_prompt
    assert "JSON-compatible dict" in ab2g_prompt


def test_ab2g_prompt_adds_generic_scaffold_without_task_specific_hints():
    task = load_pilot_tasks(MANIFEST)[0]
    frozen = frozen_payloads((task,), (2026071301,))[0]
    ab2g_prompt = build_ab2g_prompt(task, frozen)
    assert "Generic Safety-and-Format Scaffold" in ab2g_prompt
    # no leaked candidate answer values (e.g. an actual solved quotient/remainder pair)
    assert "[3, -1]" not in ab2g_prompt and '"remainder": 0' not in ab2g_prompt
    for forbidden in ("retry", "Healer", "expected_answer", "self-correct", "chain-of-thought"):
        assert forbidden.lower() not in ab2g_prompt.lower()


def test_cli_condition_defaults_to_ab1(monkeypatch):
    captured = {}

    def fake_run_pilot(tasks, **kwargs):
        captured.update(kwargs)
        return {}

    monkeypatch.setattr("agent_tools.finals_rebuild.math_boundary_pilot.run_pilot", fake_run_pilot)
    main(["--task-manifest", str(MANIFEST), "--output-root", "unused"])
    assert captured["condition"] == "ab1"


def test_run_pilot_condition_ab2g_selects_build_ab2g_prompt():
    tasks = load_pilot_tasks(MANIFEST)

    def client(url, payload, timeout):
        return {"message": {"content": "def generate(level=1, **kwargs):\n return {}"}, "prompt_eval_count": 1, "eval_count": 2}

    with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
        run_pilot(tasks, output_root=directory, run_id="pilot_ab2g", repeat_seeds=(1,), client=client, condition="ab2g")
        rows = [json.loads(line) for line in (Path(directory) / "pilot_ab2g" / "cell_results.jsonl").read_text(encoding="utf-8").splitlines()]
        assert all("Generic Safety-and-Format Scaffold" in row["prompt_text"] for row in rows)
        assert all(row["treatment"] == "Ab2g" for row in rows)
        manifest = json.loads((Path(directory) / "pilot_ab2g" / "manifest.json").read_text(encoding="utf-8"))
        assert manifest["condition"] == "ab2g"
        assert manifest["treatment"] == "Ab2g"


def test_condition_registry_maps_ab1_and_ab2g_builders():
    assert CONDITIONS["ab1"][1] is build_ab1_prompt
    assert CONDITIONS["ab2g"][1] is build_ab2g_prompt


def test_unicode_source_and_question_text_use_utf8_subprocess_io():
    source = "def generate(level=1, **kwargs):\n return {'question_text': '\\u6c42 \\u00b2 \\u7684\\u503c', 'correct_answer': 1, 'oracle_payload': {}}\n"
    status, value, error = _execute_generate(source)
    assert status == "passed", error
    assert error is None and value["question_text"] == chr(0x6C42) + " " + chr(0x00B2) + " " + chr(0x7684) + chr(0x503C)
