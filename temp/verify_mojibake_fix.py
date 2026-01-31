#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simple test: Verify mojibake removal function works correctly
Does NOT depend on Flask app or database
"""

import sys
sys.path.insert(0, 'e:\\Python\\MathProject_AST_Research')

from core.code_generator import remove_mojibake_comments

print("="*70)
print("TEST: Mojibake Removal Function Verification")
print("="*70)

# Test cases
test_cases = [
    {
        "name": "Basic mojibake in comment",
        "input": """def test():
    # 1. ?冽??? polynomial_degree (2~5) ??num_terms (2~4)??
    x = 1
    return x
""",
        "expect_clean": True,
        "expect_code_preserved": True
    },
    {
        "name": "Multiple lines with mojibake",
        "input": """def calculate():
    # Initialize with 漲 values
    # ??嚗??? setup parameters ??靽???
    a = 2
    b = 3
    # Normal setup comment
    return a + b
""",
        "expect_clean": True,
        "expect_code_preserved": True
    },
    {
        "name": "Only normal comments",
        "input": """def normal():
    # This is a normal comment
    x = 10
    # Another normal comment
    return x
""",
        "expect_clean": False,
        "expect_code_preserved": True
    },
    {
        "name": "Gemini-style corrupted comments",
        "input": """def apply_constraint():
    # 2. Ensure polynomial has Ⅱ銋 distinct terms  
    # Terms should be 蝣 and 箔-based
    # Create using sympy 喳???
    polynomial = x**2 + x + 1
    return polynomial
""",
        "expect_clean": True,
        "expect_code_preserved": True
    }
]

all_passed = True

for i, test in enumerate(test_cases, 1):
    print(f"\n[Test {i}] {test['name']}")
    print("-" * 70)
    
    result = remove_mojibake_comments(test['input'])
    
    # Check for mojibake chars
    mojibake_chars = {'冽', '嚗', '靽', '瑕', '漲', '澆', 'Ⅱ', '銋', '蝣', '箔', '喳'}
    input_has_mojibake = any(c in test['input'] for c in mojibake_chars)
    result_has_mojibake = any(c in result for c in mojibake_chars)
    
    # Check if code logic is preserved
    input_code_lines = [l.strip() for l in test['input'].split('\n') if l.strip() and not l.strip().startswith('#')]
    result_code_lines = [l.strip() for l in result.split('\n') if l.strip() and not l.strip().startswith('#')]
    code_preserved = all(code in result for code in input_code_lines if code)
    
    # Verify expectations
    clean_ok = (not result_has_mojibake) if test['expect_clean'] else True
    code_ok = code_preserved if test['expect_code_preserved'] else True
    
    test_passed = clean_ok and code_ok
    
    print(f"  Input has mojibake: {input_has_mojibake}")
    print(f"  Result has mojibake: {result_has_mojibake}")
    print(f"  Code preserved: {code_preserved}")
    print(f"  Expected clean: {test['expect_clean']}")
    print(f"  Expected code preserved: {test['expect_code_preserved']}")
    
    if test_passed:
        print(f"  ✅ PASSED")
    else:
        print(f"  ❌ FAILED")
        print(f"\n  Input:\n{test['input']}")
        print(f"\n  Result:\n{result}")
        all_passed = False

print("\n" + "="*70)
if all_passed:
    print("✅ ALL TESTS PASSED")
    print("\nConclusion:")
    print("  • Mojibake removal function is working correctly")
    print("  • Ready to integrate with Ab3 code generation")
    print("  • Code generator can safely use this function in Healer Pipeline")
else:
    print("❌ SOME TESTS FAILED")
    print("\nNeed to fix mojibake removal function")

print("="*70)
