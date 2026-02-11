# -*- coding: utf-8 -*-
"""測試統一 Healer 的功能"""

import sys
sys.path.insert(0, '/e/python/MathProject_AST_Research')

from core.healers.unified_cleanup_healer import heal_unified, UnifiedCleanupHealer
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# 測試代碼：包含重複定義、污染賦值、變量順序問題
test_code = '''
def generate_question():
    # 污染 1: 覆蓋預定義名稱
    IntegerOps = 0
    
    # 污染 2: 另一個污染
    fmt_num = 0
    
    # 污染 3: 還有一個
    clean_latex_output = None
    
    # 正常定義
    class IntegerOps:  # 這會被檢測為污染
        pass
    
    # 重複定義
    def format_output():
        return "test"
    
    def format_output():  # 這是重複定義
        return "test2"
    
    # 使用
    result = IntegerOps.random_nonzero(-50, 50)
    return result
'''

print("=" * 60)
print("測試統一 Healer")
print("=" * 60)

# 執行修復
fixed_code, total_fixes = heal_unified(test_code)

print("\n" + "=" * 60)
print("修復結果")
print("=" * 60)
print(f"總修復數量: {total_fixes}")

print("\n【修復前代碼】")
print("-" * 40)
print(test_code[:200] + "...")

print("\n【修復後代碼】")
print("-" * 40)
print(fixed_code[:300] + "...")

# 驗證是否還有污染
if 'IntegerOps = 0' in fixed_code:
    print("\n❌ 錯誤: 仍然有污染 IntegerOps = 0")
else:
    print("\n✅ 成功: 污染被移除了")

if 'fmt_num = 0' in fixed_code:
    print("❌ 錯誤: 仍然有污染 fmt_num = 0")
else:
    print("✅ 成功: 污染被移除了")

# 檢查重複定義
def_count = fixed_code.count('def format_output():')
if def_count > 1:
    print(f"❌ 錯誤: 仍然有 {def_count} 個 format_output 定義")
else:
    print("✅ 成功: 重複定義被移除了")

print("\n" + "=" * 60)
print("完成")
print("=" * 60)
