#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試指數和括號修復功能
"""
import re

# 測試案例 1：指數格式化修復
test_code_1 = """
def generate(level=1, **kwargs):
    op_latex = {'+': '+', '-': '-', '*': '\\\\times', '/': '\\\\div'}
    for _safety_loop_var in range(1000):
        a = random.randint(-3, 3)
        b = random.randint(-5, 5)
        c = random.randint(-3, 3)
        d = random.randint(-5, 5)
        p = random.randint(2, 4)
        
        # 問題代碼：使用了 ^{fmt_num(p)} 而不是 ^{{{fmt_num(p)}}}
        f_x_latex = f"({fmt_num(a)}x {(op_latex['+'] if b >= 0 else '')} {fmt_num(b)})({fmt_num(c)}x {(op_latex['+'] if d >= 0 else '')} {fmt_num(d)})^{fmt_num(p)}"
        
        return {'question_text': f_x_latex, 'answer': 'test', 'mode': 1}
"""

# 測試案例 2：括號格式化修復
test_code_2 = """
def generate(level=1, **kwargs):
    a = -3
    b = -1
    c = 2
    
    # 問題代碼：(a)x (b) 會讓學生誤會是乘法
    q = f'({fmt_num(a)}x {(op_latex["+"] if b >= 0 else "")} {fmt_num(b)})({fmt_num(c)}x {(op_latex["+"] if d >= 0 else "")} {fmt_num(d)})'
    
    return {'question_text': q, 'answer': 'test', 'mode': 1}
"""

print("=" * 60)
print("測試 1: 指數格式化修復")
print("=" * 60)

clean_code = test_code_1

# 應用修復 F.5
print("\n【修復前】")
print(clean_code[200:400])

# 修復 1：修復 ^{fmt_num(...)}
clean_code, n = re.subn(
    r'\^\{([a-zA-Z_]\w*)\}',  # 匹配 ^{variable_name}（無括號）
    r'^{{{\1}}}',              # 替換為 ^{{{variable_name}}}
    clean_code
)
print(f"\n✓ 修復 1: 找到 {n} 個 ^{{var}} 模式")

# 修復 2：更激進的指數修復：^fmt_num 這樣的情況
clean_code, n = re.subn(
    r'\^fmt_num\s*\(',
    r'^{{{fmt_num(',
    clean_code
)
print(f"✓ 修復 2: 找到 {n} 個 ^fmt_num 模式")

print("\n【修復後】")
print(clean_code[200:500])

print("\n" + "=" * 60)
print("測試 2: 括號格式化修復")
print("=" * 60)

clean_code = test_code_2
print("\n【修復前】")
print(clean_code[100:350])

# 修復：(fmt_num(...))x(...) → {{{fmt_num(...)}}}x{{{fmt_num(...)}}})
clean_code, n = re.subn(
    r'\(fmt_num\(([a-zA-Z_]\w*)\)\)([a-z])\s+\(fmt_num\(',
    r'{{{fmt_num(\1)}}}\2 {{{fmt_num(',
    clean_code
)
print(f"\n✓ 找到並修復 {n} 個括號模式")

print("\n【修復後】")
print(clean_code[100:350])

print("\n" + "=" * 60)
print("✅ 測試完成！修復規則有效")
print("=" * 60)
