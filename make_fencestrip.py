import json, re
from evalplus.data import get_human_eval_plus, get_mbpp_plus
def strip_fence(s):
    m = re.findall(r'```(?:python)?\n(.*?)```', s, re.S)
    if not m: return s
    for b in m:
        if 'def ' in b: return b
    return m[0]
DS = {'humaneval': ('he_qwen06', get_human_eval_plus),
      'mbpp':      ('mb_qwen06', get_mbpp_plus)}
for bench,(dir,fn) in DS.items():
    raw = {json.loads(l)['task_id']: json.loads(l)['raw_response']
           for l in open(f'runs/{dir}/ab1_raw.jsonl', encoding='utf-8')}
    out = f'runs/{dir}/public_benchmark_raw/{bench}/evalplus/ab1_fencestrip_itt.jsonl'
    with open(out,'w',encoding='utf-8') as f:
        for tid in fn():
            f.write(json.dumps({'task_id':tid,'solution':strip_fence(raw.get(tid,''))})+'\n')
    print('wrote', out)