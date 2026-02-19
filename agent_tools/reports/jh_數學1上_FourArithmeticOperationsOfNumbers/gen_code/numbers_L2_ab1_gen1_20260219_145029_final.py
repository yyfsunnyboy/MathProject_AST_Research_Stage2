# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfNumbers
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 293.84s | Tokens: In=471, Out=565
# Created At: 2026-02-19 14:50:29
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
from fractions import Fraction

def generate(level=1, **kwargs):
    def f_str(f, p=False):
        s = str(f.numerator) if f.denominator == 1 else f"{f.numerator}/{f.denominator}"
        if p and f < 0:
            return f"({s})"
        return s

    while True:
        try:
            n1 = random.randint(-10, 10)
            n2 = random.randint(-10, 10)
            f1 = Fraction(random.randint(-10, 10), random.randint(1, 6))
            f2 = Fraction(random.randint(-10, 10), random.randint(1, 6))
            if f2 == 0: continue
            
            n3 = random.randint(-10, 10)
            f3 = Fraction(random.randint(-10, 10), random.randint(1, 6))
            n4 = random.randint(-10, 10)
            
            term1 = ((n1 + n2) * f1) / f2
            term2 = abs(n3 * f3 + n4)
            ans = term1 + term2
            
            op1 = "+" if n2 >= 0 else "-"
            op2 = "+" if n4 >= 0 else "-"
            
            q = f"計算 [({n1}{op1}{abs(n2)})×{f_str(f1, True)}]÷{f_str(f2, True)} + |{n3}×{f_str(f3, True)}{op2}{abs(n4)}| 的值。"
            ans_s = str(ans.numerator) if ans.denominator == 1 else f"{ans.numerator}/{ans.denominator}"
            
            return {
                'question_text': q,
                'answer': '',
                'correct_answer': ans_s,
                'mode': 1
            }
        except ZeroDivisionError:
            continue

def check(user_answer, correct_answer):
    ua = str(user_answer).strip().replace(" ", "")
    ca = str(correct_answer).strip().replace(" ", "")
    is_correct = (ua == ca)
    return {
        'correct': is_correct,
        'result': '正確' if is_correct else '錯誤'
    }