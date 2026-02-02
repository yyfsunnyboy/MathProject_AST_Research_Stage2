#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""簡單測試：檢查修復後的 Domain Helper 和 MASTER_SPEC"""
import sys
sys.path.insert(0, '.')

print("=" * 60)
print("測試 1: 檢查 _coeffs_to_terms 函數是否存在")
print("=" * 60)

from core.prompts.domain_function_library import POLYNOMIAL_HELPERS

if '_coeffs_to_terms' in POLYNOMIAL_HELPERS:
    print("✅ _coeffs_to_terms 函數已添加到 POLYNOMIAL_HELPERS")
    # 提取函數定義
    lines = POLYNOMIAL_HELPERS.split('\n')
    in_function = False
    for line in lines:
        if 'def _coeffs_to_terms' in line:
            in_function = True
        if in_function:
            print(line)
            if line.strip() and not line.strip().startswith('#') and not line.strip().startswith('def') and not line.strip().startswith("'''") and in_function and line and line[0] not in ' \t':
                break
else:
    print("❌ _coeffs_to_terms 函數未找到")

print("\n" + "=" * 60)
print("測試 2: 檢查最新 MASTER_SPEC 內容")
print("=" * 60)

import sqlite3
conn = sqlite3.connect('instance/kumon_math.db')
cur = conn.cursor()

spec = cur.execute(
    'SELECT id, prompt_content FROM skill_gencode_prompt WHERE skill_id=? ORDER BY id DESC LIMIT 1',
    ('gh_ApplicationsOfDerivatives',)
).fetchone()

print(f"最新 MASTER_SPEC ID: {spec[0]}")
print(f"長度: {len(spec[1]):,} chars")

# 檢查關鍵字
keywords = ['_coeffs_to_terms', '答案格式規範', 'correct_answer =', 'polynomial1, polynomial2']
print("\n關鍵內容檢查:")
for keyword in keywords:
    if keyword in spec[1]:
        print(f"  ✅ 包含: {keyword}")
    else:
        print(f"  ❌ 缺少: {keyword}")

# 顯示答案格式部分
print("\n答案格式規範片段:")
if '答案格式規範' in spec[1]:
    idx = spec[1].index('答案格式規範')
    print(spec[1][idx:idx+500])

conn.close()

print("\n" + "=" * 60)
print("測試 3: 測試函數轉換邏輯")
print("=" * 60)

# 手動測試轉換函數
exec_globals = {}
exec(POLYNOMIAL_HELPERS, exec_globals)

_coeffs_to_terms = exec_globals['_coeffs_to_terms']
_poly_to_latex = exec_globals['_poly_to_latex']
_differentiate_poly = exec_globals['_differentiate_poly']
_poly_to_plain = exec_globals['_poly_to_plain']

# 測試用例
coeffs = [3, -5, 2]  # 3x² - 5x + 2
print(f"係數列表: {coeffs}")

terms = _coeffs_to_terms(coeffs)
print(f"轉換後 terms: {terms}")

latex_str = _poly_to_latex(terms)
print(f"LaTeX 格式: {latex_str}")

# 求導
deriv_terms = _differentiate_poly(terms, order=1)
print(f"一階導數 terms: {deriv_terms}")

deriv_str = _poly_to_plain(deriv_terms)
print(f"一階導數答案: {deriv_str}")

# 二階導數
deriv2_terms = _differentiate_poly(terms, order=2)
deriv2_str = _poly_to_plain(deriv2_terms)
print(f"二階導數答案: {deriv2_str}")

# 組裝最終答案
final_answer = f"{deriv_str}, {deriv2_str}"
print(f"\n✅ 最終答案格式: {final_answer}")

# 檢查格式
if "f'" in final_answer or '=' in final_answer or '\n' in final_answer:
    print("❌ 答案格式包含禁止符號")
else:
    print("✅ 答案格式正確")

print("\n" + "=" * 60)
print("✅ 所有測試完成")
print("=" * 60)
