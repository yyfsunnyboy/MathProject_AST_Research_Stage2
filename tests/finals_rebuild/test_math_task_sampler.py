import json, random
from pathlib import Path
from agent_tools.finals_rebuild.math_task_sampler import sample_task_parameters
TASKS=[json.loads(x) for x in (Path(__file__).parent/'fixtures'/'math_generation_tasks_ce115_pilot.jsonl').read_text().splitlines()]
def test_strata_and_determinism():
 assert len(TASKS)==12 and {t['difficulty_level'] for t in TASKS}=={1,2,3} and len({t['task_id'] for t in TASKS})==12
 for t in TASKS: assert sample_task_parameters(t,7)==sample_task_parameters(t,7)
def test_local_rng_and_samples():
 random.seed(9); before=random.random(); random.seed(9); sample_task_parameters(TASKS[0],3); after=random.random(); assert before==after
 for t in TASKS:
  for seed in range(10): assert 'oracle_payload' in sample_task_parameters(t,seed)
