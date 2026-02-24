# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfNumbers
# Model: gemini-3-flash | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 295.99s | Tokens: In=471, Out=629
# Created At: 2026-02-23 01:40:35
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
from fractions import Fraction

def generate(level=1, **kwargs):
    a = random.randint(-10, 10)
    b = random.randint(-10, 10)
    c = random.randint(1, 9)
    d = random.randint(2, 9)
    e_num = random.choice([x for x in range(-9, 10) if x != 0])
    e_den = random.randint(2, 9)
    g = random.randint(-10, 10)
    h = random.choice([x for x in range(-9, 10) if x != 0])
    i = random.randint(2, 9)
    j = random.randint(-10, 10)
    f1 = Fraction(c, d)
    f2 = Fraction(e_num, e_den)
    f3 = Fraction(h, i)
    p1 = (a + b) * f1
    p2 = p1 / f2
    p3 = abs(g * f3 + j)
    res = p2 + p3
    def fn(n):
        return f"({n})" if n < 0 else str(n)
    def ff(f):
        if f.denominator == 1:
            return fn(f.numerator)
        s = f"{f.numerator}/{f.denominator}"
        return f"({s})" if f.numerator < 0 else s
    sa = str(a)
    sb = f"+{b}" if b >= 0 else str(b)
    sf1 = ff(f1)
    sf2 = ff(f2)
    sg = fn(g)
    sf3 = ff(f3)
    sj = f"+{j}" if j >= 0 else str(j)
    q = f"[({sa}{sb})×{sf1}]÷{sf2} + |{sg}×{sf3}{sj}|"
    return {
        'question_text': f"計算 {q} 的值。",
        'answer': '',
        'correct_answer': str(res),
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        ua = str(user_answer).strip().replace(" ", "")
        ca = str(correct_answer).strip().replace(" ", "")
        if not ua:
            ok = False
        else:
            ok = Fraction(ua) == Fraction(ca)
    except:
        ok = False
    return {
        'correct': ok,
        'result': '正確' if ok else '錯誤'
    }