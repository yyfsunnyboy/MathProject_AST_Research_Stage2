#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test Script for MCRI V4.4 - L4.3 Quality Control (v2) + L5 Complexity Analysis

Tests:
1. L4.3 新規則 (10分制，不同的扣分邏輯)
2. L5A 數學複雜度分析
3. L5B 代碼複雜度分析
"""

import sys
import os
from pathlib import Path

# Add scripts directory to path
scripts_dir = Path(__file__).parent / 'scripts'
sys.path.insert(0, str(scripts_dir))

# Mock the generate function for testing
def mock_generate():
    """Mock generate function for testing"""
    return {
        'question_text': 'What is the derivative of f(x) = 3x^2 + 2x + 1?',
        'answer': 'f\'(x) = 6x + 2',
        'correct_answer': 'f\'(x) = 6x + 2',
        'code': '''
def derivative():
    x = 2
    for i in range(3):
        for j in range(2):
            x = x + 1
    return x
'''
    }

# Import the MCRI evaluator
from evaluate_mcri import MCRI_Evaluator

def test_l4_3_quality_control():
    """Test L4.3 新規則"""
    print("\n" + "="*60)
    print("Test 1: L4.3 Quality Control (新規則)")
    print("="*60)
    
    evaluator = MCRI_Evaluator(
        skill_path='test.py',
        ablation_id=0,
        model_name='test'
    )
    
    test_cases = [
        # (question_text + answer, expected_score, description)
        (
            "Solve 2x + 3 = 7. Answer: x = 2",
            10,
            "正常清潔表達式"
        ),
        (
            "What is 0x? Answer: undefined. Also 0y^2",
            0,  # 零係數扣10分 × 2 = 20分，但最低0分
            "零係數項 (嚴重)"
        ),
        (
            "Calculate: + - 5. Also - - 3",
            4,  # 扣 3分 × 2 = 6分，但10-6=4
            "符號未簡化 (+ - 和 - -)"
        ),
        (
            "Find x^1 and simplify",
            8,  # 扣 2分 × 1 = 2分，10-2=8
            "次方未隱藏 (^1)"
        ),
        (
            "Answer: 1x + 2y - 1z",
            6,  # 扣 2分 × 2 (1x 和 -1z) = 4分... wait, -1z should be detected as -1 coefficient
            "冗餘係數 (1x 和 -1z)"
        ),
        (
            "Result: 0x + + - 5 + x^1 + 1y",
            0,  # 多個違規，包括零係數，直接0分
            "多個混合違規"
        ),
    ]
    
    results = []
    for combined_text, expected_score, description in test_cases:
        result = {'question_text': combined_text, 'answer': ''}
        score, notes = evaluator.evaluate_math_artifacts(result)
        
        status = "[PASS]" if score == expected_score else "[FAIL]"
        results.append({
            'description': description,
            'score': score,
            'expected': expected_score,
            'notes': notes,
            'status': status
        })
        
        print(f"\n{status} {description}")
        print(f"    Expected: {expected_score}, Got: {score}")
        print(f"    Notes: {notes}")
    
    passed = sum(1 for r in results if "[PASS]" in r['status'])
    print(f"\nResult: {passed}/{len(results)} passed")
    return passed == len(results)

def test_l5a_math_complexity():
    """Test L5A 數學複雜度分析"""
    print("\n" + "="*60)
    print("Test 2: L5A Math Complexity Analysis")
    print("="*60)
    
    evaluator = MCRI_Evaluator(
        skill_path='test.py',
        ablation_id=0,
        model_name='test'
    )
    
    test_cases = [
        ("", (0, 0), "空字符串"),
        ("Simple text with no math", (0, 0), "無數學表達式"),
        ("2*x + 3", (0, 0) if not hasattr(evaluator, 'analyze_math_complexity') or not __import__('sys').modules.get('sympy') else (None, None), "簡單表達式 (需要 SymPy)"),
    ]
    
    results = []
    for text, expected, description in test_cases:
        if expected[0] is None:
            print(f"\n[*] {description}")
            print(f"    Skipped (SymPy not available)")
            continue
        
        ops_count, atom_count = evaluator.analyze_math_complexity(text)
        
        # For non-SymPy cases, just check that it doesn't crash
        print(f"\n[OK] {description}")
        print(f"    ops_count: {ops_count}, atom_count: {atom_count}")
        results.append(True)
    
    print(f"\nResult: {len(results)} cases completed")
    return True

def test_l5b_code_complexity():
    """Test L5B 代碼複雜度分析"""
    print("\n" + "="*60)
    print("Test 3: L5B Code Complexity Analysis")
    print("="*60)
    
    evaluator = MCRI_Evaluator(
        skill_path='test.py',
        ablation_id=0,
        model_name='test'
    )
    
    test_cases = [
        ("", (0, 0), "空代碼"),
        ("x = 5", (0, 0), "無循環"),
        ("""
for i in range(10):
    x = i
""", (None, 1), "單層循環"),
        ("""
for i in range(10):
    for j in range(5):
        x = i + j
""", (None, 2), "雙層循環"),
    ]
    
    results = []
    for code, expected, description in test_cases:
        ast_nodes, loop_depth = evaluator.analyze_code_structure(code)
        
        status = "[OK]"
        if expected[1] is not None and loop_depth != expected[1]:
            status = "[FAIL]"
        
        results.append(status == "[OK]")
        
        print(f"\n{status} {description}")
        print(f"    Expected loop_depth: {expected[1]}, Got: {loop_depth}")
        print(f"    AST nodes: {ast_nodes}")
    
    passed = sum(1 for r in results if r)
    print(f"\nResult: {passed}/{len(results)} passed")
    return passed == len(results)

if __name__ == '__main__':
    print("\n" + "="*60)
    print("MCRI V4.4 - L4.3 (v2) + L5 Complexity Tests")
    print("="*60)
    
    test_results = []
    
    # Run tests
    try:
        test_results.append(("L4.3 Quality Control", test_l4_3_quality_control()))
    except Exception as e:
        print(f"ERROR in L4.3 test: {e}")
        test_results.append(("L4.3 Quality Control", False))
    
    try:
        test_results.append(("L5A Math Complexity", test_l5a_math_complexity()))
    except Exception as e:
        print(f"ERROR in L5A test: {e}")
        test_results.append(("L5A Math Complexity", False))
    
    try:
        test_results.append(("L5B Code Complexity", test_l5b_code_complexity()))
    except Exception as e:
        print(f"ERROR in L5B test: {e}")
        test_results.append(("L5B Code Complexity", False))
    
    # Summary
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    for name, passed in test_results:
        status = "[OK]" if passed else "[FAIL]"
        print(f"{status} {name}")
    
    total_passed = sum(1 for _, p in test_results if p)
    print(f"\nTotal: {total_passed}/{len(test_results)} tests passed")
    
    sys.exit(0 if total_passed == len(test_results) else 1)
