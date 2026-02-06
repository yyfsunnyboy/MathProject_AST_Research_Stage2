#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""直接測試 generate() 函數"""
import sys
import os
from pathlib import Path

os.chdir('e:\\Python\\MathProject_AST_Research')
sys.path.insert(0, 'scripts')

from evaluate_mcri import safe_execution_context, ForbiddenInputError

# 載入技能模組
skill_file = Path('experiments/results/gh_ApplicationsOfDerivatives/gh_ApplicationsOfDerivatives_qwen2.5-coder-7b_Ab1_run01.py')

print(f"載入: {skill_file.name}")
print("="*60)

# 載入模組
import importlib.util
spec = importlib.util.spec_from_file_location("test_skill", str(skill_file))
module = importlib.util.module_from_spec(spec)

# 在安全上下文中載入
try:
    with safe_execution_context():
        spec.loader.exec_module(module)
except ForbiddenInputError as e:
    print(f"載入時被攔截: {str(e)[:60]}")

print("✅ 模組載入完成（即使被攔截）")
print(f"   hasattr(module, 'generate'): {hasattr(module, 'generate')}")

# 現在測試 generate()
if hasattr(module, 'generate'):
    print("\n執行 generate()...")
    print("="*60)
    
    try:
        with safe_execution_context():
            result = module.generate()
            print(f"✅ 成功: {result}")
    except ForbiddenInputError as e:
        print(f"✅ 被攔截: {str(e)[:60]}")
    except Exception as e:
        print(f"❌ 異常: {type(e).__name__}: {str(e)[:60]}")
else:
    print("❌ 模組沒有 generate() 函數")
