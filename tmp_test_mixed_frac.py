# -*- coding: utf-8 -*-
"""Test: mixed-number / 帶分數 題目  (-2 1/6) + 1 2/9 - (-1 1/3)"""
import sys, traceback, os
os.environ["PYTHONUTF8"] = "1"
sys.path.insert(0, r"D:\Python\MathProject_AST_Research")

from core.engine.scaler import AdaptiveScaler

SKILL_NAME   = "jh_數學1上_FourArithmeticOperationsOfNumbers"
PROBLEM_TEXT = "計算 (-2又1/6) + 1又2/9 - (-1又1/3) 的值。"
MODEL_ID     = "qwen3-vl-8b"

scaler = AdaptiveScaler(model_role='generator')
print(f"[RUN] skill={SKILL_NAME}")
print(f"[RUN] input={PROBLEM_TEXT}\n")

try:
    result = scaler.generate_custom_problems(
        skill_name=SKILL_NAME, input_text=PROBLEM_TEXT,
        count=1, model_id=MODEL_ID, ablation_mode=False,
    )
except Exception as e:
    print(f"[FATAL]\n{traceback.format_exc()}")
    sys.exit(1)

debug_meta = result.get("debug_meta", {})
generated_code = debug_meta.get("final_code", "")
problems = result.get("problems", [])

print(f"\n[GENERATED CODE] ({len(generated_code)} chars)")
print("-"*60)
print(generated_code[:2000])
print("-"*60)

if problems:
    p0 = problems[0]
    if "error" in p0:
        print(f"\n[SCALER EXEC] ERROR: {p0['error']}")
    else:
        print(f"\n[SCALER EXEC] q={p0.get('question_text','?')}")
        print(f"              ans={p0.get('correct_answer','?')}")

if not generated_code:
    print("[FAIL] debug_meta 無 final_code")
    sys.exit(1)

print("\n[EXEC] 本地 exec generate(level=1) x5:")
ok = 0
for i in range(5):
    try:
        ns = {}
        exec(compile(generated_code, "<generated>", "exec"), ns)
        if "generate" not in ns:
            print(f"  run{i+1}: ERROR - generate() not found. ns={[k for k in ns if not k.startswith('_')]}")
            continue
        out = ns["generate"](level=1)
        q = out.get("question_text", "?")
        a = out.get("correct_answer", "?")
        if q == "Error":
            print(f"  run{i+1}: Error (整除/範圍失敗)")
        else:
            print(f"  run{i+1}: {q}   ans={a}")
            ok += 1
    except Exception as e:
        print(f"  run{i+1}: EXCEPTION - {e}")
        print(traceback.format_exc(limit=3))

print(f"\n[SUMMARY] {ok}/5")
if ok >= 3:
    print("OK - 帶分數題目成功生成！")
else:
    print("FAIL")
