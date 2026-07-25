import json
from evalplus.data import get_human_eval_plus, get_mbpp_plus

def pad_to_full(samples_path, out_path, get_tasks):
    tasks = get_tasks()
    have = {}
    for line in open(samples_path, encoding='utf-8'):
        r = json.loads(line)
        have[r['task_id']] = r

    with open(out_path, 'w', encoding='utf-8') as f:
        for tid in tasks:
            if tid in have:
                f.write(json.dumps(have[tid]) + '\n')
            else:
                # 生成階段就抽取失敗 -> 用空字串佔位,必然 fail,誠實計入分母
                f.write(json.dumps({"task_id": tid, "solution": ""}) + '\n')

pad_to_full(
    "runs/he_qwen06/public_benchmark_raw/humaneval/evalplus/ab1.jsonl",
    "runs/he_qwen06/public_benchmark_raw/humaneval/evalplus/ab1_itt.jsonl",
    get_human_eval_plus,
)
pad_to_full(
    "runs/mb_qwen06/public_benchmark_raw/mbpp/evalplus/ab1.jsonl",
    "runs/mb_qwen06/public_benchmark_raw/mbpp/evalplus/ab1_itt.jsonl",
    get_mbpp_plus,
)
