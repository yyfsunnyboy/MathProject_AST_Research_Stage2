#!/usr/bin/env python3
"""
測試新的 correct_answer 格式：只有純多項式（逗號分隔）
"""
from skills.gh_ApplicationsOfDerivatives_14b_Ab2 import generate as gen_ab2
from skills.gh_ApplicationsOfDerivatives_14b_Ab3 import generate as gen_ab3

print("=" * 70)
print("測試新答案格式：純多項式（逗號分隔，無函數符號、無等號、無 LaTeX）")
print("=" * 70)

print("\n【Ab2 輸出樣本】")
for i in range(2):
    result = gen_ab2(level=1)
    print(f"\n  Run {i+1}:")
    print(f"    題目: {result['question_text']}")
    print(f"    correct_answer: {result['correct_answer']}")

print("\n【Ab3 輸出樣本】")
for i in range(2):
    result = gen_ab3(level=1)
    print(f"\n  Run {i+1}:")
    print(f"    題目: {result['question_text']}")
    print(f"    correct_answer: {result['correct_answer']}")

print("\n" + "=" * 70)

