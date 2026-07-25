import json
from evalplus.data import get_human_eval_plus, get_mbpp_plus
for name, fn in [("humaneval", get_human_eval_plus), ("mbpp", get_mbpp_plus)]:
    with open(f"tasks_{name}.jsonl", "w", encoding="utf-8") as f:
        for tid, t in fn().items():
            f.write(json.dumps({"task_id": tid, "prompt": t["prompt"],
                                "entry_point": t["entry_point"]}) + "\n")