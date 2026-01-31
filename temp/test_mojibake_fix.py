#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
快速測試亂碼修復功能
"""

import sys
sys.path.insert(0, '.')

from core.code_generator import remove_mojibake_comments

# 從實際失敗檔案中提取含亂碼的代碼片段
test_code = """import random
import math

# 1. ?冽??? polynomial_degree (2~5) ??num_terms (2~4)??
# 2. ?冽??? exponents ?"嚗Ⅱ靽?瑕漲??num_terms嚗澆 0??polynomial_degree 銋?嚗?
#    蝣箔??喳????活?詨之??1嚗誑?踹?撠?蝪∪??

def generate(level=1, **kwargs):
    '''正常的函數註解'''
    polynomial_degree = random.randint(2, 5)
    num_terms = random.randint(2, 4)
    return {
        'question_text': 'test',
        'answer': 'answer'
    }
"""

print("=" * 60)
print("測試亂碼移除功能")
print("=" * 60)

print("\n【修復前】代碼片段：")
print(test_code[:200] + "...")

result = remove_mojibake_comments(test_code)

print("\n【修復後】代碼片段：")
print(result[:200] + "...")

print("\n【驗證結果】：")
print(f"✅ 亂碼字符被移除: {'冽' not in result}")
print(f"✅ 正常代碼保留: {'def generate' in result}")
print(f"✅ 正常註解保留: {'正常的函數註解' in result}")

# 嘗試編譯修復後的代碼
try:
    compile(result, '<string>', 'exec')
    print(f"✅ 修復後的代碼可以編譯")
except SyntaxError as e:
    print(f"❌ 修復後的代碼仍有語法錯誤: {e}")

print("\n完成！")
