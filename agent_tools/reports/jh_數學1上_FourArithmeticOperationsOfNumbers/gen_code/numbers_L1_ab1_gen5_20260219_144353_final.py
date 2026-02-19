# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfNumbers
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 291.94s | Tokens: In=471, Out=582
# Created At: 2026-02-19 14:43:53
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
from fractions import Fraction

def generate(level=1, **kwargs):
    def fmt_f(f, par=False):
        s = str(f)
        if par and f < 0:
            return "(" + s + ")"
        return s
    def get_f():
        d = random.randint(2, 8)
        n = random.randint(-10, 10)
        while n == 0:
            n = random.randint(-10, 10)
        return Fraction(n, d)
    n1 = random.randint(-10, 10)
    n2 = random.randint(-10, 10)
    while n1 + n2 == 0:
        n2 = random.randint(-10, 10)
    f1 = get_f()
    f2 = get_f()
    n3 = random.randint(-10, 10)
    while n3 == 0:
        n3 = random.randint(-10, 10)
    f3 = get_f()
    n4 = random.randint(-10, 10)
    while n4 == 0:
        n4 = random.randint(-10, 10)
    t1_val = (Fraction(n1) + Fraction(n2)) * f1 / f2
    t2_val = abs(Fraction(n3) * f3 + Fraction(n4))
    ans_val = t1_val + t2_val
    inner = f"{n1}{'+' if n2 >= 0 else ''}{n2}"
    q = f"[({inner})×{fmt_f(f1, True)}]÷{fmt_f(f2, True)} + |{n3}×{fmt_f(f3, True)}{'+' if n4 >= 0 else ''}{n4}|"
    return {
        'question_text': f"計算 {q} 的值。",
        'answer': '',
        'correct_answer': str(ans_val),
        'mode': 1
    }

def check(user_answer, correct_answer):
    ua = str(user_answer).strip().replace(" ", "")
    ca = str(correct_answer).strip().replace(" ", "")
    is_correct = (ua == ca)
    return {
        'correct': is_correct,
        'result': '正確' if is_correct else '錯誤'
    }