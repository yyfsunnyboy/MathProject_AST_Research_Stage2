#!/usr/bin/env python3
"""
測試答案格式 Healer
驗證它能否正確修復常見的答案格式錯誤
"""
import sys
from core.healers.regex_healer import RegexHealer

print("=" * 70)
print("測試答案格式 Healer（第 2 層防線）")
print("=" * 70)

healer = RegexHealer()

# 測試案例 1: 包含函數符號前綴
test1 = """
def generate(level=1, **kwargs):
    ans1 = _poly_to_plain(deriv1_terms)
    ans2 = _poly_to_plain(deriv2_terms)
    a = f"f'(x) = {ans1}\\nf''(x) = {ans2}"
    return {
        'question_text': q,
        'correct_answer': a,
        'answer': a,
        'mode': 1
    }
"""

# 測試案例 2: 用逗號分隔答案
test2 = """
def generate(level=1, **kwargs):
    answers = []
    for deriv_terms in derivatives:
        ans = _poly_to_plain(deriv_terms)
        answers.append(ans)
    a = ', '.join(answers)
    return {
        'question_text': q,
        'correct_answer': a,
        'answer': a,
        'mode': 1
    }
"""

# 測試案例 3: 答案中含有 $ LaTeX 符號
test3 = """
def generate(level=1, **kwargs):
    ans1 = f"${_poly_to_plain(deriv1_terms)}$"
    ans2 = f"${_poly_to_plain(deriv2_terms)}$"
    a = f"{ans1} + {ans2}"
    return {'correct_answer': a, 'answer': a, 'mode': 1}
"""

test_cases = [
    ("包含函數符號前綴 (f'(x) =)", test1),
    ("逗號分隔答案", test2),
    ("答案含 $ LaTeX 符號", test3),
]

for i, (name, code) in enumerate(test_cases, 1):
    print(f"\n【測試 {i}】{name}")
    print("-" * 70)
    print("原始代碼：")
    print(code)
    
    fixed_code, fixes = healer.heal(code)
    
    print(f"\n修復結果（{fixes} 個修復）：")
    print(fixed_code)
    print()

print("=" * 70)
print("✅ 答案格式 Healer 測試完成")
print("=" * 70)
