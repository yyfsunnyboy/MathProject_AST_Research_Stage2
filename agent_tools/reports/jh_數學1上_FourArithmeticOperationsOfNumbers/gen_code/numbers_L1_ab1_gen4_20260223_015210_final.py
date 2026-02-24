# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfNumbers
# Model: gemini-3-flash | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 29.36s | Tokens: In=471, Out=1048
# Created At: 2026-02-23 01:52:10
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
from fractions import Fraction

def generate(level=1, **kwargs):
    def to_str(f, use_parens=False):
        if f.denominator == 1:
            s = str(f.numerator)
        else:
            s = f"{f.numerator}/{f.denominator}"
        if use_parens and f < 0:
            return f"({s})"
        return s

    template_type = random.randint(1, 3)
    
    if template_type == 1:
        # Pattern: [(a + b) × c/d] ÷ (e/f) + |g × (h/i) + j|
        a = random.randint(-10, 10)
        b = random.randint(-10, 10)
        c = Fraction(random.randint(1, 9), random.randint(2, 9))
        d = Fraction(random.randint(-9, 9), random.randint(2, 9))
        if d == 0: d = Fraction(1, 2)
        g = random.randint(-10, 10)
        h = random.randint(1, 9)
        i = random.randint(2, 9)
        j = random.randint(-10, 10)
        
        term1 = (Fraction(a + b) * c) / d
        term2 = abs(Fraction(g * h, i) + j)
        result = term1 + term2
        
        op_ab = '+' if b >= 0 else '-'
        op_j = '+' if j >= 0 else '-'
        q_text = f"[({a}{op_ab}{abs(b)}) × {to_str(c)}] ÷ {to_str(d, True)} + |{g} × {to_str(Fraction(h, i), True)} {op_j} {abs(j)}|"
        
    elif template_type == 2:
        # Pattern: (a/b + c/d) × (e/f - g/h)
        f1 = Fraction(random.randint(-9, 9), random.randint(1, 9))
        f2 = Fraction(random.randint(-9, 9), random.randint(1, 9))
        f3 = Fraction(random.randint(-9, 9), random.randint(1, 9))
        f4 = Fraction(random.randint(-9, 9), random.randint(1, 9))
        result = (f1 + f2) * (f3 - f4)
        q_text = f"({to_str(f1)} + {to_str(f2, True)}) × ({to_str(f3)} - {to_str(f4, True)})"
        
    else:
        # Pattern: a/b ÷ c/d - e/f × g/h
        f1 = Fraction(random.randint(-9, 9), random.randint(1, 9))
        f2 = Fraction(random.randint(-9, 9), random.randint(2, 9))
        if f2 == 0: f2 = Fraction(1, 1)
        f3 = Fraction(random.randint(-9, 9), random.randint(1, 9))
        f4 = Fraction(random.randint(-9, 9), random.randint(1, 9))
        result = (f1 / f2) - (f3 * f4)
        q_text = f"{to_str(f1, True)} ÷ {to_str(f2, True)} - {to_str(f3, True)} × {to_str(f4, True)}"

    if result.denominator == 1:
        correct_ans = str(result.numerator)
    else:
        correct_ans = f"{result.numerator}/{result.denominator}"
        
    return {
        'question_text': f"計算 {q_text} 的值。",
        'answer': '',
        'correct_answer': correct_ans,
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