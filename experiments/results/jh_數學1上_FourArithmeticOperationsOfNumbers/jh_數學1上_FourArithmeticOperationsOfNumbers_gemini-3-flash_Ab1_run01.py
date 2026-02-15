# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfNumbers
# Model: gemini-3-flash | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 303.48s | Tokens: In=470, Out=566
# Created At: 2026-02-15 15:54:56
# Fix Status: [No Healer - Bare LLM Output] | Fixes: Basic=0, Advanced=None
# Verification: Internal Logic Check = PASSED
# ==============================================================================

import random
from fractions import Fraction

def generate(level=1, **kwargs):
    def to_str(f, p=False):
        res = str(f.numerator) if f.denominator == 1 else f"{f.numerator}/{f.denominator}"
        return f"({res})" if p and f < 0 else res
    n1, n2 = random.randint(-10, 10), random.randint(-10, 10)
    f1 = Fraction(random.randint(1, 9), random.randint(2, 9))
    f2 = Fraction(random.choice([x for x in range(-10, 11) if x != 0]), random.randint(2, 9))
    n3 = random.choice([x for x in range(-10, 11) if x != 0])
    f3 = Fraction(random.choice([x for x in range(-10, 11) if x != 0]), random.randint(2, 9))
    n4 = random.randint(-10, 10)
    val1 = (Fraction(n1) + Fraction(n2)) * f1 / f2
    val2 = abs(Fraction(n3) * f3 + Fraction(n4))
    ans = val1 + val2
    s1 = f"{n1}+{n2}" if n2 >= 0 else f"{n1}{n2}"
    s2 = f"+{n4}" if n4 >= 0 else f"{n4}"
    q = f"計算 [({s1})×{to_str(f1)}]÷{to_str(f2, True)} + |{n3}×{to_str(f3, True)}{s2}| 的值。"
    return {
        'question_text': q,
        'answer': '',
        'correct_answer': to_str(ans),
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        u = user_answer.strip().replace(" ", "")
        c = correct_answer.strip().replace(" ", "")
        if u == c:
            return {'correct': True, 'result': '正確'}
        if Fraction(u) == Fraction(c):
            return {'correct': True, 'result': '正確'}
    except:
        pass
    return {'correct': False, 'result': '錯誤'}