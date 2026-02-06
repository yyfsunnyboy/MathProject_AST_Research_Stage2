# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: qwen2.5-coder-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 24.10s | Tokens: In=617, Out=451
# Created At: 2026-02-06 20:13:18
# Fix Status: [Basic Cleanup Only] | Fixes: Basic=1, Advanced=None
# Verification: Internal Logic Check = FAILED
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
    op1 = safe_choice(['+', '-', '*', '/'])
    op2 = safe_choice(['+', '-', '*', '/'])

    # 計算正確答案
    if op1 == '+':
        result1 = num1 + num2
    elif op1 == '-':
        result1 = num1 - num2
    elif op1 == '*':
        result1 = num1 * num2
    else:
        result1 = num1 / num2

    if op2 == '+':
        result2 = num3 + num4
    elif op2 == '-':
        result2 = num3 - num4
    elif op2 == '*':
        result2 = num3 * num4
    else:
        result2 = num3 / num4

    # 計算最終答案
    final_result = (result1 + result2) * 3 + abs(num5 * (-2) - 5)

    # 組合題目文字
    question_text = f"計算 [{num1} {op1} {num2}] ÷ {num4} × 3 + |{num5} × (-2) - 5| 的值。"

    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': str(final_result),
        'mode': 1
    }

def check(user_answer, correct_answer):
    if user_answer.strip() == correct_answer:
        return {'correct': True, 'result': '正確'}
    else:
        return {'correct': False, 'result': '錯誤'}