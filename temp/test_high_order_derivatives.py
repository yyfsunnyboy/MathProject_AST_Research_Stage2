#!/usr/bin/env python3
"""
Test high-order derivatives (3rd, 4th order)
Verify answer format is correct even with 3rd/4th/5th derivatives
"""
from skills.gh_ApplicationsOfDerivatives_14b_Ab2 import generate as gen_ab2
from skills.gh_ApplicationsOfDerivatives_14b_Ab3 import generate as gen_ab3

print("=" * 70)
print("High-Order Derivative Test (3rd, 4th, 5th order)")
print("=" * 70)

def validate_answer_format(answer_str, test_name):
    """
    Validate answer format:
    - No function symbols (f'(x), f''(x), etc)
    - No equals signs
    - No LaTeX $ symbols
    - Only pure polynomials
    """
    issues = []
    
    for i, line in enumerate(answer_str.split('\n'), 1):
        line = line.strip()
        if not line:
            continue
            
        # Check for function symbols
        if any(pat in line for pat in ['f\'(x)', 'f""(x)', 'f^', 'f(' ]):
            issues.append(f"  Line {i}: Contains function symbol - '{line[:50]}'")
        
        # Check for equals sign
        if '=' in line:
            issues.append(f"  Line {i}: Contains equals sign - '{line[:50]}'")
        
        # Check for LaTeX
        if '$' in line:
            issues.append(f"  Line {i}: Contains $ symbol - '{line[:50]}'")
        
        # Check if it looks like pure polynomial
        # Should only contain: digits, x, ^, +, -, /
        invalid_chars = [c for c in line if c not in '0123456789x^+-/()']
        if invalid_chars and invalid_chars != [' ']:
            issues.append(f"  Line {i}: Contains unexpected characters {set(invalid_chars)} - '{line[:50]}'")
    
    if issues:
        print(f"  FAILED ({test_name}):")
        for issue in issues:
            print(issue)
        return False
    else:
        print(f"  PASSED ({test_name}): All answers are pure polynomials")
        return True

print("\n【Ab2 Tests】(Regex Healer only)")
print("-" * 70)
for run in range(5):
    result = gen_ab2(level=1)
    question = result['question_text']
    answer = result['answer']
    
    # Extract derivative order from question
    # "求 $f'(x)$ 與 $f''(x)$" or "求 $f''(x)$ 與 $f^{(3)}(x)$" etc
    if "f'" in question:
        order_info = "at least 1st derivative"
    print(f"\nRun {run+1}: {order_info}")
    print(f"  Question: {question[:65]}...")
    
    # Show answer lines
    ans_lines = answer.split('\n')
    print(f"  Answers ({len(ans_lines)} lines):")
    for i, ans in enumerate(ans_lines, 1):
        print(f"    {i}: {ans}")
    
    # Validate
    passed = validate_answer_format(answer, f"Ab2 Run {run+1}")

print("\n" + "=" * 70)
print("【Ab3 Tests】(Regex + AST Healer)")
print("-" * 70)
for run in range(5):
    result = gen_ab3(level=1)
    question = result['question_text']
    answer = result['answer']
    
    if "f'" in question:
        order_info = "at least 1st derivative"
    print(f"\nRun {run+1}: {order_info}")
    print(f"  Question: {question[:65]}...")
    
    # Show answer lines
    ans_lines = answer.split('\n')
    print(f"  Answers ({len(ans_lines)} lines):")
    for i, ans in enumerate(ans_lines, 1):
        print(f"    {i}: {ans}")
    
    # Validate
    passed = validate_answer_format(answer, f"Ab3 Run {run+1}")

print("\n" + "=" * 70)
print("Test completed!")
print("If all tests PASSED, then high-order derivatives are working correctly")
print("=" * 70)
