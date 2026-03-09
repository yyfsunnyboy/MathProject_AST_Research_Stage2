# -*- coding: utf-8 -*-
"""真正呼叫 Qwen3-VL 8B 生成出題程式"""
import sys, traceback
sys.path.insert(0, r"D:\Python\MathProject_AST_Research")

from core.engine.scaler import AdaptiveScaler
from core.code_generator import _inject_domain_libs

SKILL_NAME   = "jh_數學1上_FourArithmeticOperationsOfIntegers"
PROBLEM_TEXT = "計算 | 8*(-2)-5 | div 7*(-3) 的值。"
MODEL_ID     = "qwen3-vl-8b"

scaler = AdaptiveScaler(model_role='generator')
print(f"[RUN] 呼叫 {MODEL_ID}\n")

try:
    result = scaler.generate_custom_problems(
        skill_name=SKILL_NAME, input_text=PROBLEM_TEXT,
        count=1, model_id=MODEL_ID, ablation_mode=False,
    )
except Exception as e:
    print(f"[FATAL]\n{traceback.format_exc()}")
    sys.exit(1)

# final_code is in debug_meta; problems[] holds execution results from scaler._execute_code
debug_meta = result.get("debug_meta", {})
generated_code = debug_meta.get("final_code", "")
problems = result.get("problems", [])

print(f"\n[GENERATED CODE] ({len(generated_code)} chars)")
print("-"*60)
print(generated_code[:2000])
print("-"*60)

# Also show what scaler already executed (first problem result)
if problems:
    p0 = problems[0]
    if "error" in p0:
        print(f"\n[SCALER EXEC RESULT] ERROR: {p0['error']}")
    else:
        print(f"\n[SCALER EXEC RESULT] q={p0.get('question_text','?')}  ans={p0.get('correct_answer','?')}")

if not generated_code:
    print("[FAIL] debug_meta 無 final_code")
    sys.exit(1)

print("\n[EXEC] 本地 exec generate(level=1) x3:")
ok = 0
for i in range(3):
    try:
        ns = {}
        exec(compile(generated_code, "<generated>", "exec"), ns)
        if "generate" not in ns:
            print(f"  run{i+1}: ERROR - generate() not defined after exec")
            print(f"  ns keys: {[k for k in ns if not k.startswith('_')]}")
            continue
        out = ns["generate"](level=1)
        q, a = out.get("question_text","?"), out.get("correct_answer","?")
        if q == "Error":
            print(f"  run{i+1}: Error (整除失敗 - scaffold placeholder)")
        else:
            print(f"  run{i+1}: {q}  ans={a}")
            ok += 1
    except Exception as e:
        print(f"  run{i+1}: ERROR - {e}")
        print(traceback.format_exc(limit=3))

print(f"\n[SUMMARY] {ok}/3")
if ok >= 2:
    print("OK: Qwen3-VL 成功生成可執行的出題程式！")
else:
    print("FAIL")