#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""測試改進的模組載入"""
import sys
import os
from pathlib import Path

os.chdir('e:\\Python\\MathProject_AST_Research')
sys.path.insert(0, 'scripts')

from evaluate_mcri import safe_execution_context, ForbiddenInputError
import importlib.util

skill_file = Path('experiments/results/gh_ApplicationsOfDerivatives/gh_ApplicationsOfDerivatives_qwen2.5-coder-7b_Ab1_run01.py')

print(f"嘗試載入: {skill_file.name}")
print("="*60)

spec = importlib.util.spec_from_file_location("test_skill", str(skill_file))
module = importlib.util.module_from_spec(spec)

# 策略1：完全忽略 ForbiddenInputError
try:
    print("開始載入模組...")
    with safe_execution_context():
        spec.loader.exec_module(module)
    print("✅ 載入成功（無異常）")
except ForbiddenInputError as e:
    print(f"⚠️  在安全上下文中被攔截，但模組仍存在")
except Exception as e:
    print(f"❌ 其他異常: {type(e).__name__}: {str(e)[:60]}")

# 檢查 generate 是否存在
print(f"\ngenerate() 是否存在: {hasattr(module, 'generate')}")

if hasattr(module, 'generate'):
    print("\n嘗試執行 generate()...")
    print("="*60)
    
    try:
        result = module.generate()
        print(f"✅ 成功執行，結果:")
        for key, val in result.items():
            print(f"   {key}: {str(val)[:60]}")
    except Exception as e:
        print(f"❌ 異常: {type(e).__name__}: {str(e)[:60]}")
