# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfNumbers
# Model: gemini-3-flash | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 54.74s | Tokens: In=471, Out=473
# Created At: 2026-02-23 02:36:30
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
from fractions import Fraction

def generate(level=1, **kwargs):
    def get_f():
        d = random.randint(2, 6)
        n = random.randint(-9, 9)
        while n == 0:
            n = random.randint(-9, 9)
        return Fraction(n, d)
    
    def s(val, lead=False):
        if val >= 0:
            return str(val)
        return str(val) if lead else f"({val})"

    n1 = random.randint(-10, 10)
    n2 = random.randint(-10, 10)
    f1 = get_f()
    f2 = get_f()
    n3 = random.randint(-10, 10)
    f3 = get_f()
    n4 = random.randint(-10, 10)

    v1 = (Fraction(n1) + Fraction(n2)) * f1 / f2
    v2 = abs(Fraction(n3) * f3 + Fraction(n4))
    ans = v1 + v2

    q = f"[({s(n1, True)}+{s(n2)})×{s(f1)}]÷{s(f2)} + |{s(n3, True)}×{s(f3)}+{s(n4)}|"

    return {
        'question_text': f"計算 {q} 的值。",
        'answer': '',
        'correct_answer': str(ans),
        'mode': 1
    }

def check(user_answer, correct_answer):
    from fractions import Fraction
    try:
        ua = user_answer.strip().replace(" ", "")
        ca = correct_answer.strip().replace(" ", "")
        res = (Fraction(ua) == Fraction(ca))
    except:
        res = False
    return {
        'correct': res,
        'result': '正確' if res else '錯誤'
    }