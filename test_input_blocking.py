#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""測試 input() 攔截機制"""
import sys
import os
from pathlib import Path
from io import StringIO

os.chdir('e:\\Python\\MathProject_AST_Research')
sys.path.insert(0, 'scripts')

# 載入技能模組
skill_file = Path('experiments/results/gh_ApplicationsOfDerivatives/gh_ApplicationsOfDerivatives_qwen2.5-coder-7b_Ab1_run01.py')
spec = __import__('importlib.util').util.spec_from_file_location("skill_module", skill_file)
module = __import__('importlib.util').util.module_from_spec(spec)

# 模擬被攔截的 input() 函數
def blocked_input(prompt=''):
    raise EOFError("❌ 生成的代碼包含 input() 調用，不符合自動評估要求")

# 重定向並測試
print("開始測試 input() 攔截...")
print("="*80)

old_stdout = sys.stdout
old_stdin = sys.stdin
old_input = __builtins__.get('input') if isinstance(__builtins__, dict) else getattr(__builtins__, 'input')

sys.stdout = StringIO()
sys.stdin = StringIO()

if isinstance(__builtins__, dict):
    __builtins__['input'] = blocked_input
else:
    setattr(__builtins__, 'input', blocked_input)

try:
    spec.loader.exec_module(module)
    
    # 嘗試調用 generate()
    print("嘗試調用 generate()...", file=old_stdout)
    result = module.generate()
    print(f"✅ 成功生成: {result}", file=old_stdout)
    
except EOFError as e:
    print(f"✅ 成功攔截 input(): {e}", file=old_stdout)
    
except Exception as e:
    print(f"❌ 其他異常: {type(e).__name__}: {e}", file=old_stdout)

finally:
    sys.stdout = old_stdout
    sys.stdin = old_stdin
    if isinstance(__builtins__, dict):
        __builtins__['input'] = old_input
    else:
        setattr(__builtins__, 'input', old_input)

print("\n✅ 測試完成")
