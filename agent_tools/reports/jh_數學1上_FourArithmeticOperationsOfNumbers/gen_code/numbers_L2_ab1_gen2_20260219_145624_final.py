# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfNumbers
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 47.80s | Tokens: In=471, Out=619
# Created At: 2026-02-19 14:56:24
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
from fractions import Fraction

def generate(level=1, **kwargs):
    def f_str(f, p=False):
        s = str(f.numerator) if f.denominator == 1 else f"{f.numerator}/{f.denominator}"
        return f"({s})" if p and f < 0 else s
    
    a = random.randint(-10, 10)
    b = random.randint(-10, 10)
    c = Fraction(random.randint(-9, 9), random.randint(1, 9))
    while c == 0:
        c = Fraction(random.randint(1, 9), random.randint(1, 9))
    
    d = Fraction(random.randint(-9, 9), random.randint(1, 9))
    while d == 0:
        d = Fraction(random.randint(1, 9), random.randint(1, 9))
        
    e = random.randint(-10, 10)
    f = Fraction(random.randint(-9, 9), random.randint(1, 9))
    while f == 0:
        f = Fraction(random.randint(1, 9), random.randint(1, 9))
        
    g = random.randint(-10, 10)
    
    v1 = ((Fraction(a) + Fraction(b)) * c) / d
    v2 = abs(Fraction(e) * f + Fraction(g))
    ans = v1 + v2
    
    ans_str = str(ans.numerator) if ans.denominator == 1 else f"{ans.numerator}/{ans.denominator}"
    
    op_b = "+" if b >= 0 else ""
    op_g = "+" if g >= 0 else ""
    
    q_text = f"計算 [({a}{op_b}{b})×{f_str(c, True)}]÷{f_str(d, True)} + |{e}×{f_str(f, True)}{op_g}{g}| 的值。"
    
    return {
        'question_text': q_text,
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