# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: gemini-3-flash | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 297.89s | Tokens: In=460, Out=455
# Created At: 2026-02-22 23:46:51
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random

def generate(level=1, **kwargs):
    v3 = random.choice([i for i in range(-10, 11) if i not in [0, 1, -1]])
    res = random.randint(-10, 10)
    v12 = v3 * res
    v1 = random.randint(-30, 30)
    v2 = v12 - v1
    v4 = random.choice([i for i in range(-10, 11) if i != 0])
    v5 = random.randint(-10, 10)
    v6 = random.randint(-10, 10)
    v7 = random.randint(-30, 30)
    def p(n):
        return f"({n})" if n < 0 else str(n)
    expr1 = f"[{p(v1)}+{p(v2)}]÷{p(v3)}×{p(v4)}"
    if v7 >= 0:
        expr2 = f"|{p(v5)}×{p(v6)}+{v7}|"
    else:
        expr2 = f"|{p(v5)}×{p(v6)}-{abs(v7)}|"
    question_text = f"計算 {expr1}+{expr2} 的值。"
    correct_val = (res * v4) + abs(v5 * v6 + v7)
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': str(correct_val),
        'mode': 1
    }

def check(user_answer, correct_answer):
    is_correct = str(user_answer).strip() == str(correct_answer).strip()
    return {
        'correct': is_correct,
        'result': '正確' if is_correct else '錯誤'
    }