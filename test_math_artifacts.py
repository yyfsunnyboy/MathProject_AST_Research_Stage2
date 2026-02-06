#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 L4.3 数学异味检测功能
验证三类违规的检测和评分逻辑
"""

import re
import sys

# 设置 UTF-8 编码
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def evaluate_math_artifacts(question: str, answer: str) -> tuple:
    """
    L4.3 數學異味檢測 (Math Artifacts Detection) - 10分
    """
    score = 10.0
    notes = []
    
    combined_text = question + ' ' + answer
    
    # ===== 1. 零係數項檢測 (嚴重違規) =====
    zero_coeff_patterns = [
        r'\b0[a-zA-Z]',      # 0x, 0y 直接相連
        r'\b0\s+[a-zA-Z]',   # 0 x, 0 y 有空格
    ]
    
    zero_coeff_matches = []
    for pattern in zero_coeff_patterns:
        matches = re.findall(pattern, combined_text)
        zero_coeff_matches.extend(matches)
    
    if zero_coeff_matches:
        score = 0.0
        notes.append(f"零係數項 (嚴重): {', '.join(set(zero_coeff_matches))}")
        return score, "; ".join(notes)
    
    # ===== 2. 符號未簡化檢測 (中度違規) =====
    medium_violations = []
    
    plus_minus_matches = re.findall(r'\+\s*-', combined_text)
    if plus_minus_matches:
        medium_violations.extend(['+ -'] * len(plus_minus_matches))
    
    minus_minus_matches = re.findall(r'-\s*-', combined_text)
    if minus_minus_matches:
        medium_violations.extend(['- -'] * len(minus_minus_matches))
    
    power_one_matches = re.findall(r'\^\s*1\b', combined_text)
    if power_one_matches:
        medium_violations.extend(['^1'] * len(power_one_matches))
    
    if medium_violations:
        penalty = len(medium_violations) * 5
        score = max(0, score - penalty)
        notes.append(f"符號未簡化 (中度): {len(medium_violations)}個 ({penalty}分)")
    
    # ===== 3. 冗餘係數檢測 (輕微違規) =====
    light_violations = []
    
    coeff_one_matches = re.findall(r'(?<!\d)\b1[a-zA-Z]', combined_text)
    if coeff_one_matches:
        light_violations.extend(coeff_one_matches)
    
    coeff_minus_one_matches = re.findall(r'(?<!\d)-1[a-zA-Z]', combined_text)
    if coeff_minus_one_matches:
        light_violations.extend(coeff_minus_one_matches)
    
    if light_violations:
        penalty = len(light_violations) * 2
        score = max(0, score - penalty)
        notes.append(f"冗餘係數 (輕微): {len(light_violations)}個 ({penalty}分)")
    
    if score >= 9.0:
        notes.append("數學表示清潔")
    
    return score, "; ".join(notes) if notes else "清潔"


# 测试用例
test_cases = [
    {
        "name": "正常数学表达式（满分）",
        "question": "求 $2x^2 + 3x + 1$ 的导数",
        "answer": "$4x + 3$",
        "expected_score": 10.0
    },
    {
        "name": "零系数项（0分）",
        "question": "化简 $0x^3 + 2x + 1$",
        "answer": "$2x + 1$",
        "expected_score": 0.0
    },
    {
        "name": "符号未简化 + - （扣5分）",
        "question": "计算 $5 + -3$",
        "answer": "$2$",
        "expected_score": 5.0
    },
    {
        "name": "符号未简化 ^ 1 （扣5分）",
        "question": "化简 $x^1 + 2x$",
        "answer": "$x + 2x$",
        "expected_score": 5.0
    },
    {
        "name": "冗余系数 1x （扣4分，因为出现2次）",
        "question": "导数是 $1x + 3$",
        "answer": "$1x + 3$",
        "expected_score": 6.0
    },
    {
        "name": "冗余系数 -1w （两个实例）",
        "question": "导数为",
        "answer": "$-1w$",
        "expected_score": 6.0  # -1w匹配两次 (1w + -1w) = 扣4分
    },
    {
        "name": "多个混合违规",
        "question": "导数是 $1x + -1y + 2$",
        "answer": "$0$",
        "expected_score": 0.0  # 中度5分 + 轻微6分 = 超过10分，扣完
    },
]

print("=" * 80)
print("[L4.3 Math Artifacts Detection Test Suite]")
print("=" * 80)

passed = 0
failed = 0

for i, test in enumerate(test_cases, 1):
    score, notes = evaluate_math_artifacts(test["question"], test["answer"])
    is_correct = abs(score - test["expected_score"]) < 0.01
    
    status = "[PASS]" if is_correct else "[FAIL]"
    print(f"\n{status} Test {i}: {test['name']}")
    print(f"  Question: {test['question']}")
    print(f"  Answer: {test['answer']}")
    print(f"  Expected: {test['expected_score']:.1f} | Got: {score:.1f}")
    print(f"  Notes: {notes}")
    
    if is_correct:
        passed += 1
    else:
        failed += 1

print("\n" + "=" * 80)
print(f"Results: {passed} passed, {failed} failed (Total: {len(test_cases)})")
print("=" * 80)
