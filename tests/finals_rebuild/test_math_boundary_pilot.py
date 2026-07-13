import json
import tempfile
from pathlib import Path

from agent_tools.finals_rebuild.math_boundary_pilot import TASK_IDS, classify_response, frozen_payloads, load_pilot_tasks, run_pilot


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


def test_mock_run_writes_required_artifacts():
    tasks = load_pilot_tasks(MANIFEST)
    def client(url, payload, timeout):
        return {"message": {"content": "def generate(level=1, **kwargs):\n return {}"}, "prompt_eval_count": 1, "eval_count": 2}
    with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
        summary = run_pilot(tasks, output_root=directory, run_id="pilot", repeat_seeds=(1, 2, 3), client=client)
        root = Path(directory) / "pilot"
        assert summary["total_cells"] == 30
        assert {path.name for path in root.iterdir()} >= {"manifest.json", "frozen_payloads.jsonl", "cell_results.jsonl", "summary.json", "failure_examples.jsonl"}
