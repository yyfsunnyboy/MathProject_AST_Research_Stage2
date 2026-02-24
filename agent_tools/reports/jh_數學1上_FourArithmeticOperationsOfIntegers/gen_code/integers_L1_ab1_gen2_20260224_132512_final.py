# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 22.11s | Tokens: In=630, Out=939
# Created At: 2026-02-24 13:25:12
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random

def generate(level=1, **kwargs):
    question_text = ""
    answer = ""
    correct_answer = ""
    mode = 1

    if level == 1:
        num1 = random.randint(-50, 50)
        num2 = random.randint(-50, 50)
        num3 = random.randint(-50, 50)
        num4 = random.randint(-50, 50)
        num5 = random.randint(-50, 50)
        num6 = random.randint(-50, 50)
        op1 = random.choice(['+', '-'])
        op2 = random.choice(['+', '-'])
        op3 = random.choice(['+', '-'])
        op4 = random.choice(['+', '-'])
        op5 = random.choice(['+', '-'])
        abs_flag = random.choice([True, False])
        question_text = f"計算 $[{num1}{op1}{num2}{op2}{num3}]÷{num4}×{num5}{op3}{abs_flag and f'|{num6}|' or ''}$ 的值。"
        expr = f"({num1}{op1}{num2}{op2}{num3}) // {num4} * {num5} {op3} {abs_flag and f'abs({num6})' or ''}"
        correct_answer = str(eval(expr))
    elif level == 2:
        num1 = random.randint(-100, 100)
        num2 = random.randint(-100, 100)
        num3 = random.randint(-100, 100)
        num4 = random.randint(-100, 100)
        num5 = random.randint(-100, 100)
        num6 = random.randint(-100, 100)
        op1 = random.choice(['+', '-', '*'])
        op2 = random.choice(['+', '-', '*'])
        op3 = random.choice(['+', '-', '*'])
        op4 = random.choice(['+', '-', '*'])
        op5 = random.choice(['+', '-', '*'])
        abs_flag = random.choice([True, False])
        question_text = f"計算 $[{num1}{op1}{num2}{op2}{num3}]÷{num4}×{num5}{op3}{abs_flag and f'|{num6}|' or ''}$ 的值。"
        expr = f"({num1}{op1}{num2}{op2}{num3}) // {num4} * {num5} {op3} {abs_flag and f'abs({num6})' or ''}"
        correct_answer = str(eval(expr))
    else:
        num1 = random.randint(-200, 200)
        num2 = random.randint(-200, 200)
        num3 = random.randint(-200, 200)
        num4 = random.randint(-200, 200)
        num5 = random.randint(-200, 200)
        num6 = random.randint(-200, 200)
        op1 = random.choice(['+', '-', '*', '//'])
        op2 = random.choice(['+', '-', '*', '//'])
        op3 = random.choice(['+', '-', '*', '//'])
        op4 = random.choice(['+', '-', '*', '//'])
        op5 = random.choice(['+', '-', '*', '//'])
        abs_flag = random.choice([True, False])
        question_text = f"計算 $[{num1}{op1}{num2}{op2}{num3}]÷{num4}×{num5}{op3}{abs_flag and f'|{num6}|' or ''}$ 的值。"
        expr = f"({num1}{op1}{num2}{op2}{num3}) // {num4} * {num5} {op3} {abs_flag and f'abs({num6})' or ''}"
        correct_answer = str(eval(expr))

    return {
        'question_text': question_text,
        'answer': answer,
        'correct_answer': correct_answer,
        'mode': mode
    }

def check(user_answer, correct_answer):
    correct = user_answer == correct_answer
    result = '正確' if correct else '錯誤'
    return {
        'correct': correct,
        'result': result
    }