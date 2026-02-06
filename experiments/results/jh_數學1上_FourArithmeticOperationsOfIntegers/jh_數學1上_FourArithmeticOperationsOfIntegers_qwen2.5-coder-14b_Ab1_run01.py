# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: qwen2.5-coder-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 30.79s | Tokens: In=617, Out=514
# Created At: 2026-02-06 20:12:53
# Fix Status: [Basic Cleanup Only] | Fixes: Basic=1, Advanced=None
# Verification: Internal Logic Check = FAILED
# ==============================================================================

import random

def generate(level=1, **kwargs):
    # 生成隨機數字
    num1 = random.randint(-50, 50)
    num2 = random.randint(-50, 50)
    num3 = random.randint(1, 50)
    num4 = random.randint(-50, 50)
    
    # 隨機選擇運算符
    op1 = safe_choice(['+', '-', '*', '/'])
    op2 = safe_choice(['+', '-', '*', '/'])
    op3 = safe_choice(['+', '-'])
    
    # 確保除數不為零
    while num3 == 0:
        num3 = random.randint(1, 50)
    
    # 生成題目文字
    question_text = f"計算 [ ({num1}){op1}({num2}) ]{op2}(-{num3})×{num4} +｜{num4}{op3}(-{num4})-{num4}｜的值。"
    
    # 計算正確答案
    if op1 == '+':
        part1 = num1 + num2
    elif op1 == '-':
        part1 = num1 - num2
    elif op1 == '*':
        part1 = num1 * num2
    else:
        part1 = num1 / num2
    
    if op2 == '+':
        part2 = part1 + (-num3)
    elif op2 == '-':
        part2 = part1 - (-num3)
    elif op2 == '*':
        part2 = part1 * (-num3)
    else:
        part2 = part1 / (-num3)
    
    part3 = part2 * num4
    
    if op3 == '+':
        part4 = num4 + (-num4) - num4
    else:
        part4 = num4 - (-num4) - num4
    
    correct_answer = str(part3 + abs(part4))
    
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    if user_answer.strip() == correct_answer:
        return {'correct': True, 'result': '正確'}
    else:
        return {'correct': False, 'result': '錯誤'}