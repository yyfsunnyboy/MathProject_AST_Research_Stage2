# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfNumbers
# Model: gemini-3-flash | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 308.81s | Tokens: In=470, Out=617
# Created At: 2026-02-15 16:00:06
# Fix Status: [No Healer - Bare LLM Output] | Fixes: Basic=0, Advanced=None
# Verification: Internal Logic Check = PASSED
# ==============================================================================

import random
from fractions import Fraction

def generate(level=1, **kwargs):
    def get_f(allow_zero=True):
        while True:
            n = random.randint(-9, 9)
            if not allow_zero and n == 0:
                continue
            d = random.randint(2, 9)
            return Fraction(n, d)

    def f_str(f, p=True):
        s = f"{f.numerator}/{f.denominator}" if f.denominator != 1 else str(f.numerator)
        if p and f < 0:
            return f"({s})"
        return s

    def i_str(i, p=True):
        if p and i < 0:
            return f"({i})"
        return str(i)

    a = random.randint(-10, 10)
    b = random.randint(-10, 10)
    c = get_f(allow_zero=False)
    d = get_f(allow_zero=False)
    e = random.randint(-10, 10)
    f = get_f(allow_zero=False)
    g = random.randint(-10, 10)

    val = ((Fraction(a) + Fraction(b)) * c) / d + abs(Fraction(e) * f + Fraction(g))

    sa = i_str(a, False)
    sb = f"+{b}" if b >= 0 else str(b)
    sc = f_str(c, True)
    sd = f_str(d, True)
    se = i_str(e, False)
    sf = f_str(f, True)
    sg = f"+{g}" if g >= 0 else str(g)

    q_text = f"計算 [({sa}{sb})×{sc}]÷{sd} + |{se}×{sf}{sg}| 的值。"
    ans_str = f"{val.numerator}/{val.denominator}" if val.denominator != 1 else str(val.numerator)

    return {
        'question_text': q_text,
        'answer': '',
        'correct_answer': ans_str,
        'mode': 1
    }

def check(user_answer, correct_answer):
    ua = str(user_answer).strip().replace(' ', '')
    ca = str(correct_answer).strip().replace(' ', '')
    is_correct = (ua == ca)
    return {
        'correct': is_correct,
        'result': '正確' if is_correct else '錯誤'
    }