#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Loop Breaker V2.0 Test"""

import sys
sys.path.insert(0, 'e:/Python/MathProject_AST_Research')

from core.healers.regex_healer import RegexHealer
import ast

# Test case: simplified Ab3 failure scenario
test_code = """
def generate(level=1, **kwargs):
    while True:
        value = 10
        if value > 5:
            break
    result_list = []
    if len(result_list) != 2:
        continue
    return {'answer': 1}
"""

print("=" * 60)
print("Loop Breaker V2.0 Test")
print("=" * 60)

print("\nOriginal Code (with error):")
print(test_code)

print("\n" + "=" * 60)
print("Running Regex Healer...")
print("=" * 60)

healer = RegexHealer()
fixed_code, fixes = healer.heal(test_code)

print("\nFixes applied:", fixes)
print("\nFixed Code:")
print(fixed_code)

print("\n" + "=" * 60)
print("AST Validation")
print("=" * 60)

try:
    ast.parse(fixed_code)
    print("\n[PASS] AST parse successful! Code is syntactically correct!")
    print("[SUCCESS] Loop Breaker V2.0 test passed!")
except SyntaxError as e:
    print(f"\n[FAIL] AST parse failed: {e}")
    print("[FAIL] Loop Breaker V2.0 test failed!")

print("\n" + "=" * 60)
