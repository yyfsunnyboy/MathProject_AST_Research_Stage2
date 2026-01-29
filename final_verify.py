#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""最終驗證新生成的gh_ApplicationsOfDerivatives_14B_Ab3"""

from skills.gh_ApplicationsOfDerivatives_14B_Ab3 import generate
import time

print("=" * 70)
print("【最終驗證 gh_ApplicationsOfDerivatives_14B_Ab3】")
print("=" * 70)

# 條件 1: 無限迴圈
print("\n1️⃣  檢查無限迴圈...")
all_fast = True
for i in range(10):
    start = time.time()
    result = generate()
    elapsed = time.time() - start
    if elapsed > 1.0:
        print(f"   ❌ 第 {i+1} 次耗時 {elapsed:.2f}s（超過1s）")
        all_fast = False
        break
    print(f"   ✅ 第 {i+1} 次耗時 {elapsed:.4f}s")

if all_fast:
    print("   ✅ 所有執行都在1s內完成，無無限迴圈")

# 條件 2&3&4: 格式
print("\n2️⃣  檢查格式品質...")
for i in range(3):
    result = generate()
    q = result['question_text']
    a = result['correct_answer']
    
    has_dollar_q = "$" in q
    has_dollar_a = "$" in a
    has_backslash_a = "\\" in a
    
    print(f"\n   【第{i+1}個樣本】")
    print(f"      題目: {q[:80]}...")
    print(f"      答案: {a}")
    print(f"      - 題目有$: {has_dollar_q}")
    print(f"      - 答案有$: {has_dollar_a} (應該False)")
    print(f"      - 答案有\\\\: {has_backslash_a} (應該False)")
    
    if has_dollar_a or has_backslash_a:
        print(f"      ⚠️  警告：答案不乾淨")

print("\n" + "=" * 70)
print("✅ 驗證完成！")
print("=" * 70)
