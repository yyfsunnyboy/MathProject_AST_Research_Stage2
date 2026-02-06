#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test the LaTeX Formatter healer"""
import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '.')

from core.healers.regex_healer import RegexHealer

# Test code with problematic clean_latex_output pattern
test_code = """
def generate(level=1, **kwargs):
    n1 = -26
    n2 = 29
    n3 = -12
    n4 = -6
    
    op_latex = {'+': '+', '-': '-', '*': '\\\\times', '/': '\\\\div'}
    math_expr_str = f'[ {fmt_num(n1)} + {fmt_num(n2)} ] \\\\times {fmt_num(n3)} \\\\times {fmt_num(n4)}'
    q = f'計算 {math_expr_str} 的值。'

    def clean_latex_output(s):
        return s.replace('[', '$[').replace(']', ']$')
    q = clean_latex_output(q)
    a = str(final_answer)
    return {'question_text': q, 'correct_answer': a, 'answer': a, 'mode': 1}
"""

print("=" * 80)
print("Test: LaTeX Formatter Healer")
print("=" * 80)
print("\n[Original Code]")
print(test_code)

healer = RegexHealer()
fixed_code, fixes = healer.heal(test_code)

print("\n" + "=" * 80)
print(f"[Result] {fixes} fixes applied")
print("=" * 80)
print("\n[Fixed Code]")
print(fixed_code)

# Check if the problematic patterns were removed
has_clean_latex_func = 'def clean_latex_output' in fixed_code
has_clean_latex_call = 'q = clean_latex_output(q)' in fixed_code

print("\n" + "=" * 80)
print("[Verification]")
print("=" * 80)
print(f"✓ clean_latex_output function removed: {not has_clean_latex_func}")
print(f"✓ clean_latex_output call removed: {not has_clean_latex_call}")
print(f"✓ Total fixes: {fixes}")
