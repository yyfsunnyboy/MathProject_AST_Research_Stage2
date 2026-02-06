# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: qwen2.5-coder-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 22.62s | Tokens: In=617, Out=518
# Created At: 2026-02-06 14:06:52
# Fix Status: [Basic Cleanup Only] | Fixes: Basic=1, Advanced=None
# Verification: Internal Logic Check = PASSED
# ==============================================================================

import random

def generate(level=1, **kwargs):
    # 生成隨機數字
    num1 = random.randint(-50, 50)
    num2 = random.randint(-50, 50)
    num3 = random.randint(1, 50) if level == 1 else random.randint(-50, 50)
    num4 = random.randint(1, 50) if level == 1 else random.randint(-50, 50)
    
    # 隨機選擇運算符
    op1 = random.choice(['+', '-', '*', '/'])
    op2 = random.choice(['+', '-', '*', '/'])
    op3 = random.choice(['+', '-'])
    
    # 確保除數不為零
    while num3 == 0:
        num3 = random.randint(1, 50)
    while num4 == 0:
        num4 = random.randint(1, 50)
    
    # 生成題目文字
    question_text = f"計算 [ ({num1}){op1}({num2}) ]{op2}({num3})×{num4} +｜{num4}{op3}({num2}-5)｜的值。"
    
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
        part2 = part1 + num3
    elif op2 == '-':
        part2 = part1 - num3
    elif op2 == '*':
        part2 = part1 * num3
    else:
        part2 = part1 / num3
    
    part3 = abs(num4 * (num2 - 5))
    
    correct_answer = str(part2 * num4 + part3)
    
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    return {
        'correct': user_answer == correct_answer,
        'result': '正確' if user_answer == correct_answer else '錯誤'
    }