# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfNumbers
# Model: gemini-3-flash | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 50.43s | Tokens: In=471, Out=579
# Created At: 2026-02-23 02:04:33
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
from fractions import Fraction

def generate(level=1, **kwargs):
    def fmt_frac(f, paren=False):
        s = str(f.numerator) if f.denominator == 1 else f"{f.numerator}/{f.denominator}"
        if paren and f.numerator < 0:
            return f"({s})"
        return s
    a = random.randint(-9, 9)
    b = random.randint(-9, 9)
    if a + b == 0: b = random.randint(1, 9)
    f1 = Fraction(random.randint(-5, 5) or 1, random.randint(2, 6))
    f2 = Fraction(random.randint(-5, 5) or -5, random.randint(2, 6))
    g = random.randint(-9, 9) or 8
    f3 = Fraction(random.randint(-5, 5) or -1, random.randint(2, 6))
    j = random.randint(-9, 9) or -5
    term1 = (Fraction(a + b) * f1) / f2
    term2 = abs(Fraction(g) * f3 + Fraction(j))
    ans = term1 + term2
    sa, sb = str(a), (f"+{b}" if b >= 0 else str(b))
    sc, se = fmt_frac(f1, True), fmt_frac(f2, True)
    sg, sh, sj = str(g), fmt_frac(f3, True), (f"+{j}" if j >= 0 else str(j))
    q_text = f"計算 [({sa}{sb})×{sc}]÷{se} + |{sg}×{sh}{sj}| 的值。"
    ans_str = str(ans.numerator) if ans.denominator == 1 else f"{ans.numerator}/{ans.denominator}"
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