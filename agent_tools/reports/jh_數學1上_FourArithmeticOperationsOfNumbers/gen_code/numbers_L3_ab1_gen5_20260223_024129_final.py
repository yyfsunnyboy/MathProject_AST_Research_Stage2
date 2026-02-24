# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfNumbers
# Model: gemini-3-flash | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 297.04s | Tokens: In=471, Out=533
# Created At: 2026-02-23 02:41:29
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
from fractions import Fraction

def generate(level=1, **kwargs):
    def f_str(f, bracket=False):
        s = str(f.numerator) if f.denominator == 1 else f"{f.numerator}/{f.denominator}"
        return f"({s})" if bracket and f < 0 else s

    def get_nz_f():
        while True:
            n, d = random.randint(-9, 9), random.randint(1, 6)
            if n != 0: return Fraction(n, d)

    v1, v2 = random.randint(-9, 9), random.randint(-9, 9)
    v3, v4 = get_nz_f(), get_nz_f()
    v5, v6 = random.randint(-9, 9), get_nz_f()
    v7 = random.randint(-9, 9)

    res1 = (Fraction(v1) + Fraction(v2)) * v3 / v4
    res2 = abs(Fraction(v5) * v6 + Fraction(v7))
    final_res = res1 + res2

    op1 = "+" if v2 >= 0 else ""
    op2 = "+" if v7 >= 0 else ""
    
    q = f"[({v1}{op1}{v2})×{f_str(v3, True)}]÷{f_str(v4, True)} + |{v5}×{f_str(v6, True)}{op2}{v7}|"
    ans_str = str(final_res.numerator) if final_res.denominator == 1 else f"{final_res.numerator}/{final_res.denominator}"
    
    return {
        'question_text': f"計算 {q} 的值。",
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