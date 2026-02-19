# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfNumbers
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 295.11s | Tokens: In=471, Out=846
# Created At: 2026-02-19 15:06:27
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
from fractions import Fraction

def generate(level=1, **kwargs):
    def _fmt(f, p=False):
        s = str(f)
        return f"({s})" if p and f < 0 else s

    t = random.randint(1, 3)
    if t == 1:
        n1, n2 = random.randint(-10, 10), random.randint(-10, 10)
        f1 = Fraction(random.randint(1, 9), random.randint(2, 9))
        f2_num = random.choice([i for i in range(-9, 10) if i != 0])
        f2 = Fraction(f2_num, random.randint(2, 9))
        n3, n4 = random.randint(1, 10), random.randint(-10, 10)
        f3 = Fraction(random.choice([-1, 1]) * random.randint(1, 9), random.randint(2, 9))
        res_a = ((n1 + n2) * f1) / f2
        res_b = abs(n3 * f3 + n4)
        ans = res_a + res_b
        q = f"[({n1}{'+' if n2>=0 else ''}{n2})×{_fmt(f1)}]÷{_fmt(f2, True)} + |{n3}×{_fmt(f3, True)}{'+' if n4>=0 else ''}{n4}|"
    elif t == 2:
        f1 = Fraction(random.randint(-9, 9), random.randint(2, 9))
        f2 = Fraction(random.randint(-9, 9), random.randint(2, 9))
        f3 = Fraction(random.randint(-9, 9), random.randint(2, 9))
        f4 = Fraction(random.randint(-9, 9), random.randint(2, 9))
        ans = (f1 - f2) * (f3 + f4)
        q = f"({_fmt(f1)} - {_fmt(f2, True)}) × ({_fmt(f3)} + {_fmt(f4, True)})"
    else:
        f1 = Fraction(random.randint(-9, 9), random.randint(2, 9))
        f2_num = random.choice([i for i in range(-9, 10) if i != 0])
        f2 = Fraction(f2_num, random.randint(2, 9))
        f3 = Fraction(random.randint(-9, 9), random.randint(2, 9))
        f4 = Fraction(random.randint(-9, 9), random.randint(2, 9))
        ans = (f1 / f2) - (f3 * f4)
        q = f"{_fmt(f1)} ÷ {_fmt(f2, True)} - {_fmt(f3, True)} × {_fmt(f4, True)}"

    return {
        'question_text': f"計算 {q} 的值。",
        'answer': '',
        'correct_answer': str(ans),
        'mode': 1
    }

def check(user_answer, correct_answer):
    u = str(user_answer).replace(" ", "")
    c = str(correct_answer).replace(" ", "")
    is_correct = u == c
    return {
        'correct': is_correct,
        'result': '正確' if is_correct else '錯誤'
    }