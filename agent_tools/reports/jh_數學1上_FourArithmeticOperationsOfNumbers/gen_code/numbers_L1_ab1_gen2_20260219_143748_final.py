# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfNumbers
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 298.61s | Tokens: In=471, Out=505
# Created At: 2026-02-19 14:37:48
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
from fractions import Fraction

def generate(level=1, **kwargs):
    def f_str(f):
        s = str(f.numerator) if f.denominator == 1 else f"{f.numerator}/{f.denominator}"
        return f"({s})" if f.numerator < 0 else s
    
    a = random.randint(-10, 10)
    b = random.randint(-10, 10)
    c = Fraction(random.randint(-9, 9), random.randint(2, 6))
    d = Fraction(random.choice([i for i in range(-9, 10) if i != 0]), random.randint(2, 6))
    e = random.randint(-10, 10)
    f = Fraction(random.randint(-9, 9), random.randint(2, 6))
    g = random.randint(-10, 10)
    
    res = ((Fraction(a + b) * c) / d) + abs(Fraction(e) * f + g)
    
    op_b = "+" if b >= 0 else "-"
    op_g = "+" if g >= 0 else "-"
    
    q = f"[({a}{op_b}{abs(b)})×{f_str(c)}]÷{f_str(d)} + |{e}×{f_str(f)}{op_g}{abs(g)}|"
    
    ans_str = str(res.numerator) if res.denominator == 1 else f"{res.numerator}/{res.denominator}"
    
    return {
        'question_text': f"計算 {q} 的值。",
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