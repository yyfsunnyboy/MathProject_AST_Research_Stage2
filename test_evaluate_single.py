#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""測試評分系統如何處理 input() 被攔截的情況"""
import sys
import os
from pathlib import Path

os.chdir('e:\\Python\\MathProject_AST_Research')
sys.path.insert(0, 'scripts')

# 匯入評估器
from evaluate_mcri import MCRI_Evaluator

# 載入一個包含 input() 的技能
skill_file = Path('experiments/results/gh_ApplicationsOfDerivatives/gh_ApplicationsOfDerivatives_qwen2.5-coder-7b_Ab1_run01.py')

print(f"測試評分: {skill_file.name}")
print("="*80)

# 初始化評估器 (需要提供 ablation_id)
evaluator = MCRI_Evaluator(skill_file, ablation_id='Ab1')
if not evaluator.load_skill_module():
    print("❌ 模組載入失敗")
    sys.exit(1)

print(f"✅ 模組載入成功")
print(f"Skill: {evaluator.skill_name}")

# 執行單次評估
print("\n執行單次評估...")
item = evaluator.evaluate_single_repetition(1)

print(f"\n結果:")
print(f"  Status: {item.get('status')}")
print(f"  Error: {item.get('error_log')}")
print(f"  Included in Avg: {item.get('included_in_avg')}")
print(f"  L1 Total: {item.get('score_l1_total')}")
print(f"  L2 Total: {item.get('score_l2_total')}")
print(f"  L3 Total: {item.get('score_l3_total')}")
print(f"  L4 Total: {item.get('score_l4_total')}")
total_score = item.get('score_l1_total', 0) + item.get('score_l2_total', 0) + item.get('score_l3_total', 0) + item.get('score_l4_total', 0)
print(f"  總分: {total_score}/100")

if item.get('status') == 'INPUT_BLOCKED' or item.get('status') == 'FAIL':
    print("\n✅ 成功檢測並標記為失敗（input() 被攔截）")
else:
    print(f"\n⚠️  未正確標記為失敗: {item.get('status')}")
