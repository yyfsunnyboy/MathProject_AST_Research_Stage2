# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfNumbers
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 27.11s | Tokens: In=471, Out=560
# Created At: 2026-02-19 14:38:18
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
from fractions import Fraction

def generate(level=1, **kwargs):
    def fmt_f(n, d):
        if d == 1:
            return str(n)
        if n < 0:
            return f"({n}/{d})"
        return f"{n}/{d}"

    a = random.randint(-10, 10)
    b = random.randint(-10, 10)
    c = random.randint(1, 9)
    d = random.randint(2, 9)
    e = random.choice([i for i in range(-9, 10) if i != 0])
    f = random.randint(2, 9)
    g = random.randint(-10, 10)
    h = random.choice([i for i in range(-9, 10) if i != 0])
    i = random.randint(2, 9)
    j = random.randint(-10, 10)
    
    op = random.choice(['+', '-'])
    
    q_part1 = f"[({a}{'+' if b>=0 else ''}{b})×{c}/{d}]÷{fmt_f(e, f)}"
    q_part2 = f"|{g}×{fmt_f(h, i)}{'+' if j>=0 else ''}{j}|"
    question = f"計算 {q_part1} {op} {q_part2} 的值。"
    
    val1 = (Fraction(a) + Fraction(b)) * Fraction(c, d) / Fraction(e, f)
    val2 = abs(Fraction(g) * Fraction(h, i) + Fraction(j))
    
    if op == '+':
        ans = val1 + val2
    else:
        ans = val1 - val2
        
    return {
        'question_text': question,
        'answer': '',
        'correct_answer': str(ans),
        'mode': 1
    }

def check(user_answer, correct_answer):
    ua = str(user_answer).strip().replace(" ", "")
    ca = str(correct_answer).strip().replace(" ", "")
    is_correct = ua == ca
    return {
        'correct': is_correct,
        'result': '正確' if is_correct else '錯誤'
    }