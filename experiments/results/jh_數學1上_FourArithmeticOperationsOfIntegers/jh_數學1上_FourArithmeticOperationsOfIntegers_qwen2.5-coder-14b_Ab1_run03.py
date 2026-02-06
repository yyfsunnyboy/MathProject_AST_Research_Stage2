# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: qwen2.5-coder-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 22.86s | Tokens: In=617, Out=516
# Created At: 2026-02-06 14:06:29
# Fix Status: [Basic Cleanup Only] | Fixes: Basic=1, Advanced=None
# Verification: Internal Logic Check = PASSED
# ==============================================================================

import random

def generate(level=1, **kwargs):
    # 生成隨機整數
    num1 = random.randint(-50, 50)
    num2 = random.randint(-50, 50)
    num3 = random.randint(-50, 50)
    num4 = random.randint(1, 50)  # 確保除數不為零
    num5 = random.randint(-50, 50)

    # 隨機選擇運算符
    op1 = random.choice(['+', '-', '*', '/'])
    op2 = random.choice(['+', '-', '*', '/'])
    op3 = random.choice(['+', '-'])

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
        part2 = num3 + num4
    elif op2 == '-':
        part2 = num3 - num4
    elif op2 == '*':
        part2 = num3 * num4
    else:
        part2 = num3 / num4

    abs_value = abs(num5 * (-2) - 5)

    correct_answer = ((part1 / num4) * 3 + abs_value)
    
    # 格式化題目文字
    question_text = f"計算 [ ({num1}){op1}({num2}) ]{op2}(-{num4})×3 +｜{num5}×(-2)-5｜的值。"

    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': str(correct_answer),
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        user_answer = float(user_answer)
        correct_answer = float(correct_answer)
        if abs(user_answer - correct_answer) < 1e-6:  # 考慮浮點數精度問題
            return {'correct': True, 'result': '正確'}
        else:
            return {'correct': False, 'result': '錯誤'}
    except ValueError:
        return {'correct': False, 'result': '錯誤'}