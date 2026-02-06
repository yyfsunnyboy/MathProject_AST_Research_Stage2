#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""測試安全上下文"""
import sys
import os
from pathlib import Path

os.chdir('e:\\Python\\MathProject_AST_Research')
sys.path.insert(0, 'scripts')

from evaluate_mcri import safe_execution_context, ForbiddenInputError

print('測試 safe_execution_context...')
print("="*60)

caught_error = None
try:
    with safe_execution_context():
        # 在安全上下文中的代碼
        try:
            user_input = input("這應該被攔截: ")
        except ForbiddenInputError as e:
            caught_error = e
except Exception as e:
    print(f"❌ 外層異常: {type(e).__name__}: {e}")

# 在安全上下文外列印結果
if caught_error:
    print(f"✅ 成功捕捉 ForbiddenInputError")
    print(f"   訊息: {str(caught_error)[:80]}")
else:
    print("❌ 沒有捕捉到異常")

print("\n✅ 安全上下文測試完成")
