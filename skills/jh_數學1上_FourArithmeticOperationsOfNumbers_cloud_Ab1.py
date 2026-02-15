# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfNumbers
# Model: gemini-3-flash-preview | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 330.90s | Tokens: In=470, Out=641
# Created At: 2026-02-15 14:31:10
# Fix Status: [Clean Pass] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PASSED
# ==============================================================================
import random
from fractions import Fraction

def generate(level=1, **kwargs):
    a = random.randint(-10, 10)
    b = random.randint(-10, 10)
    while a + b == 0:
        b = random.randint(-10, 10)
    c_n = random.randint(1, 5)
    c_d = random.randint(2, 5)
    c = Fraction(c_n, c_d)
    d_n = random.choice([-5, -4, -3, -2, 2, 3, 4, 5])
    d_d = random.choice([2, 3, 5])
    d = Fraction(d_n, d_d)
    e = random.randint(2, 12)
    f_d = random.choice([2, 3, 4, 6])
    f = Fraction(-1, f_d)
    g = random.randint(-8, -1)
    v1 = Fraction(a + b)
    v2 = v1 * c
    v3 = v2 / d
    v4 = abs(e * f + g)
    res = v3 + v4
    def _f(n, p=False):
        s = f"{n.numerator}/{n.denominator}" if n.denominator != 1 else str(n.numerator)
        if p and n < 0:
            return f"({s})"
        return s
    p_a = f"({a}+{b})" if b >= 0 else f"({a}{b})"
    expr = f"[{p_a}×{_f(c)}]÷{_f(d, True)} + |{e}×{_f(f, True)}{g if g < 0 else '+'+str(g)}|"
    ans_str = f"{res.numerator}/{res.denominator}" if res.denominator != 1 else str(res.numerator)
    return {
        'question_text': f"計算 {expr} 的值。",
        'answer': '',
        'correct_answer': ans_str,
        'mode': 1
    }

def check(user_answer, correct_answer):
    from fractions import Fraction
    try:
        u_str = user_answer.strip().replace(' ', '')
        c_str = correct_answer.strip().replace(' ', '')
        is_correct = Fraction(u_str) == Fraction(c_str)
    except:
        is_correct = user_answer.strip() == correct_answer.strip()
    return {
        'correct': is_correct,
        'result': '正確' if is_correct else '錯誤'
    }