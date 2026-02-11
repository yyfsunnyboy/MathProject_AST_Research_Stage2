#!/usr/bin/env python3
import sys
sys.path.append(r'e:\python\MathProject_AST_Research')

# 清除缓存
for mod in list(sys.modules.keys()):
    if 'jh_數學1上_FourArithmeticOperationsOfIntegers' in mod:
        del sys.modules[mod]

import skills.jh_數學1上_FourArithmeticOperationsOfIntegers_14b_Ab3 as ab3
import random

# 設定種子以便重現
random.seed(42)

print("="*80)
print("AB3 問題文本生成追蹤")
print("="*80)

# 模擬 generate() 函數的部分邏輯
print("\n1. 生成基本變數...")

op1 = random.choice(['+', '-', '*', '/'])
op2 = random.choice(['+', '-', '*', '/'])
C = ab3.IntegerOps.random_nonzero(-10, 10)

print(f"   op1 = {op1}, op2 = {op2}, C = {C}")

# 直接調用 generate 並檢查中間結果
print("\n2. 調用 generate()...")
result = ab3.generate(level=1)

print(f"   最終問題: {result['question_text']}")
print(f"   答案: {result['correct_answer']}")

# 測試 clean_latex_output 函數
print("\n3. 測試 clean_latex_output()...")

test_strings = [
    r"計算 $\left[ ((-24) + 2) - 10 \right] - \left| (-1) + (-3) \right|$ 的值。",
    r"計算 $\left[ (2 \times (-10)) \times (-3) \right] - \left| (-5) + 14 \right|$ 的值。",
]

for i, test_str in enumerate(test_strings):
    print(f"\n   測試 {i+1}:")
    print(f"   輸入: {test_str[:60]}...")
    output = ab3.clean_latex_output(test_str)
    print(f"   輸出: {output[:60]}...")
    print(f"   是否相同: {test_str == output}")

print("\n" + "="*80)
