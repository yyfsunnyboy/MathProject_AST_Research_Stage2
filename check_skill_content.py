#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""簡單測試：直接看生成的代碼是否有 input()"""
import sys
import os
from pathlib import Path

os.chdir('e:\\Python\\MathProject_AST_Research')
sys.path.insert(0, 'scripts')

# 載入一個技能檔案
skill_file = Path('experiments/results/gh_ApplicationsOfDerivatives/gh_ApplicationsOfDerivatives_qwen2.5-coder-7b_Ab1_run01.py')

print(f"檢查檔案: {skill_file.name}")
print("="*80)

with open(skill_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 檢查是否有 input()
if 'input(' in content:
    print("⚠️  檔案包含 input() 調用！")
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        if 'input(' in line:
            print(f"  行 {i}: {line.strip()}")
else:
    print("✅ 檔案沒有 input() 調用")

# 檢查代碼是否能正常編譯
try:
    compile(content, skill_file.name, 'exec')
    print("✅ 代碼語法正確")
except SyntaxError as e:
    print(f"❌ 語法錯誤: {e}")
