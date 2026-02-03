#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Answer Format Healer
Verify it can fix common answer format errors
"""
import sys
import os

# Force UTF-8 output on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from core.healers.regex_healer import RegexHealer

print("=" * 70)
print("Testing Answer Format Healer (Level 2 Defense)")
print("=" * 70)

healer = RegexHealer()

# Test case 1: Contains function symbol prefix
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

# Test case 2: Uses comma separator
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

# Test case 3: Answer contains $ LaTeX symbols
test3 = """
def generate(level=1, **kwargs):
    ans1 = f"${_poly_to_plain(deriv1_terms)}$"
    ans2 = f"${_poly_to_plain(deriv2_terms)}$"
    a = f"{ans1} + {ans2}"
    return {'correct_answer': a, 'answer': a, 'mode': 1}
"""

test_cases = [
    ("Contains function symbol prefix (f'(x) =)", test1),
    ("Comma separator in answers", test2),
    ("Answer contains $ LaTeX symbols", test3),
]

for i, (name, code) in enumerate(test_cases, 1):
    print(f"\n[Test {i}] {name}")
    print("-" * 70)
    print("Original code:")
    print(code)
    
    try:
        fixed_code, fixes = healer.heal(code)
        
        print(f"\nFixed code ({fixes} fixes):")
        print(fixed_code)
    except Exception as e:
        print(f"Error: {e}")
    print()

print("=" * 70)
print("Answer Format Healer test completed")
print("=" * 70)
