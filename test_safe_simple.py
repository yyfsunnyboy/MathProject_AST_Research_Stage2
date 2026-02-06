#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""簡單測試 safe_execution_context()"""
import sys
import os

os.chdir('e:\\Python\\MathProject_AST_Research')
sys.path.insert(0, 'scripts')

from evaluate_mcri import safe_execution_context, ForbiddenInputError

# 測試 1: 測試 print() 被靜音
print("測試 1: print() 被靜音")
print("="*60)
print("在安全上下文外:")
print("外層文字")

with safe_execution_context():
    print("這應該被靜音")

print("安全上下文後恢復")

# 測試 2: 測試 input() 被攔截
print("\n測試 2: input() 被攔截")
print("="*60)

error_caught = None
try:
    with safe_execution_context():
        # 這應該拋異常
        user_input = input("提示: ")
except ForbiddenInputError as e:
    error_caught = e

if error_caught:
    print(f"✅ 成功攔截")
else:
    print(f"❌ 沒有攔截")
