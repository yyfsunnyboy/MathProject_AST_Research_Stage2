import sys
sys.path.insert(0, '.')

from scripts.evaluate_mcri import MCRI_Evaluator

# 測試 7B Ab2 run01
print("="*80)
print("測試 7B Ab2 run01")
print("="*80)

ev = MCRI_Evaluator(
    'experiments/results/jh_數學1上_FourArithmeticOperationsOfIntegers/jh_數學1上_FourArithmeticOperationsOfIntegers_qwen2.5-coder-7b_Ab2_run01.py',
    2,
    'qwen2.5-coder-7b'
)

result = ev.load_skill_module()
print(f"載入結果: {result}")
if ev.module:
    print(f"有 generate: {hasattr(ev.module, 'generate')}")
    print(f"有 check: {hasattr(ev.module, 'check')}")
