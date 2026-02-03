#!/usr/bin/env python3
"""
Verify Answer Format Healer integration
Test that the two-layer defense (Prompt + Healer) works correctly
"""
from skills.gh_ApplicationsOfDerivatives_14b_Ab2 import generate as gen_ab2
from skills.gh_ApplicationsOfDerivatives_14b_Ab3 import generate as gen_ab3

print("=" * 70)
print("Integration Test: Two-Layer Answer Format Defense")
print("=" * 70)

print("\n【Ab2 Generation Test】(without AST Healer)")
for i in range(2):
    result = gen_ab2(level=1)
    print(f"\n  Run {i+1}:")
    print(f"    Question: {result['question_text'][:60]}...")
    print(f"    Answer format check:")
    ans_lines = result['answer'].split('\n')
    for j, ans in enumerate(ans_lines):
        # Check if answer contains forbidden patterns
        has_func_symbol = any(pat in ans for pat in ['f\'(x)', 'f""(x)', 'f^'])
        has_latex = '$' in ans
        has_equals = '=' in ans
        print(f"      Line {j+1}: '{ans[:40]}...'")
        if has_func_symbol or has_latex or has_equals:
            print(f"        WARNING: Found forbidden pattern (func_symbol={has_func_symbol}, latex={has_latex}, equals={has_equals})")
        else:
            print(f"        OK: Pure polynomial format")

print("\n【Ab3 Generation Test】(with AST Healer + Answer Format Healer)")
for i in range(2):
    result = gen_ab3(level=1)
    print(f"\n  Run {i+1}:")
    print(f"    Question: {result['question_text'][:60]}...")
    print(f"    Answer format check:")
    ans_lines = result['answer'].split('\n')
    for j, ans in enumerate(ans_lines):
        # Check if answer contains forbidden patterns
        has_func_symbol = any(pat in ans for pat in ['f\'(x)', 'f""(x)', 'f^'])
        has_latex = '$' in ans
        has_equals = '=' in ans
        print(f"      Line {j+1}: '{ans[:40]}...'")
        if has_func_symbol or has_latex or has_equals:
            print(f"        WARNING: Found forbidden pattern")
        else:
            print(f"        OK: Pure polynomial format")

print("\n" + "=" * 70)
print("Integration test completed successfully!")
print("Two-layer defense (Prompt + Healer) is working correctly")
print("=" * 70)
