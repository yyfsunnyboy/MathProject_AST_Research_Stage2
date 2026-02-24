# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfNumbers
# Model: gemini-3-flash | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 42.09s | Tokens: In=471, Out=377
# Created At: 2026-02-23 02:34:06
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
from fractions import Fraction

def generate(level=1, **kwargs):
    def f_s(f, p=False):
        s = str(f)
        return f"({s})" if p and f < 0 else s
    while True:
        try:
            v = []
            for _ in range(7):
                n = random.randint(-10, 10)
                d = random.randint(1, 5)
                while n == 0:
                    n = random.randint(-10, 10)
                v.append(Fraction(n, d))
            a, b, c, d, e, f, g = v
            val = ((a + b) * c / d) + abs(e * f + g)
            txt = f"計算 [({f_s(a)} + {f_s(b, True)}) × {f_s(c, True)}] ÷ {f_s(d, True)} + |{f_s(e)} × {f_s(f, True)} + {f_s(g, True)}| 的值。"
            return {
                'question_text': txt,
                'answer': '',
                'correct_answer': str(val),
                'mode': 1
            }
        except ZeroDivisionError:
            continue

def check(user_answer, correct_answer):
    is_correct = str(user_answer).strip() == str(correct_answer).strip()
    return {
        'correct': is_correct,
        'result': '正確' if is_correct else '錯誤'
    }