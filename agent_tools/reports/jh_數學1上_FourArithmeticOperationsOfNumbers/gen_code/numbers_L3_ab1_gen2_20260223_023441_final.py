# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfNumbers
# Model: gemini-3-flash | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 32.51s | Tokens: In=471, Out=667
# Created At: 2026-02-23 02:34:41
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
from fractions import Fraction

def generate(level=1, **kwargs):
    a = random.randint(-10, 10)
    b = random.randint(-10, 10)
    while a + b == 0:
        b = random.randint(-10, 10)
    c_n = random.randint(1, 9)
    c_d = random.randint(2, 9)
    c = Fraction(c_n, c_d)
    e_n = random.choice([i for i in range(-9, 10) if i != 0])
    e_d = random.randint(2, 9)
    e = Fraction(e_n, e_d)
    g = random.randint(-10, 10)
    while g == 0:
        g = random.randint(-10, 10)
    h_n = random.choice([i for i in range(-9, 10) if i != 0])
    h_d = random.randint(2, 9)
    h = Fraction(h_n, h_d)
    j = random.randint(-10, 10)
    p1 = (Fraction(a + b) * c) / e
    p2 = abs(Fraction(g) * h + Fraction(j))
    res = p1 + p2
    def f_int(n):
        return f"({n})" if n < 0 else str(n)
    def f_frac(f):
        if f.denominator == 1:
            return f_int(f.numerator)
        n, d = f.numerator, f.denominator
        return f"({n}/{d})" if n < 0 else f"{n}/{d}"
    expr = f"[({f_int(a)}+{f_int(b)})×{f_frac(c)}]÷{f_frac(e)} + |{f_int(g)}×{f_frac(h)}+{f_int(j)}|"
    expr = expr.replace("+-", "-").replace("--", "+").replace("(+", "(")
    ans_str = str(res.numerator) if res.denominator == 1 else f"{res.numerator}/{res.denominator}"
    return {
        'question_text': f"計算 {expr} 的值。",
        'answer': '',
        'correct_answer': ans_str,
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