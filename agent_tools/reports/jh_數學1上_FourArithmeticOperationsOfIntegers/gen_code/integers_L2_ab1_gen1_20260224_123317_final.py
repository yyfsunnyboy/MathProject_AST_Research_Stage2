# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: gemini-3-flash | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 29.62s | Tokens: In=460, Out=459
# Created At: 2026-02-24 12:33:17
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random

def generate(level=1, **kwargs):
    a = random.randint(-50, 50)
    b = random.randint(-50, 50)
    s = a + b
    divs = [i for i in range(-20, 21) if i != 0 and s % i == 0]
    c = random.choice(divs) if divs else 1
    d = random.randint(-10, 10)
    e = random.randint(-15, 15)
    f = random.randint(-15, 15)
    g = random.randint(-50, 50)
    def f_str(n, b=True):
        return "(" + str(n) + ")" if n < 0 and b else str(n)
    p1 = "[" + f_str(a) + "+" + f_str(b) + "]÷" + f_str(c) + "×" + f_str(d)
    p2 = "|" + f_str(e, False) + "×" + f_str(f) + "-" + f_str(g) + "|"
    op = random.choice(["+", "-"])
    q = "計算 " + p1 + op + p2 + " 的值。"
    v1 = (a + b) // c * d
    v2 = abs(e * f - g)
    res = v1 + v2 if op == "+" else v1 - v2
    return {
        'question_text': q,
        'answer': '',
        'correct_answer': str(res),
        'mode': 1
    }

def check(user_answer, correct_answer):
    is_ok = str(user_answer).strip() == str(correct_answer).strip()
    return {
        'correct': is_ok,
        'result': '正確' if is_ok else '錯誤'
    }