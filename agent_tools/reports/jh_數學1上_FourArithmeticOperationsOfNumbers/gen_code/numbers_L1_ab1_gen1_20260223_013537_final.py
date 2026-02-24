# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfNumbers
# Model: gemini-3-flash | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 38.07s | Tokens: In=471, Out=507
# Created At: 2026-02-23 01:35:37
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
from fractions import Fraction

def generate(level=1, **kwargs):
    def fstr(n, p=False):
        s = str(n)
        if p and n < 0:
            return f"({s})"
        return s
    
    a = random.randint(-10, 10)
    b = random.randint(-10, 10)
    c = Fraction(random.randint(1, 9), random.randint(2, 9))
    d_n = random.randint(1, 9) * random.choice([-1, 1])
    d = Fraction(d_n, random.randint(2, 9))
    e = random.randint(-10, 10)
    f_n = random.randint(1, 9) * random.choice([-1, 1])
    f = Fraction(f_n, random.randint(2, 9))
    g = random.randint(-10, 10)
    
    val1 = (a + b) * c
    val2 = val1 / d
    val3 = abs(e * f + g)
    ans = val2 + val3
    
    s_ab = f"{a}{'+' if b>=0 else ''}{b}"
    s_efg = f"{e}×{fstr(f, True)}{'+' if g>=0 else ''}{g}"
    expr = f"[({s_ab})×{fstr(c, True)}]÷{fstr(d, True)} + |{s_efg}|"
    
    return {
        'question_text': f"計算 {expr} 的值。",
        'answer': '',
        'correct_answer': str(ans),
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