# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: gemini-3-flash | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 43.69s | Tokens: In=460, Out=837
# Created At: 2026-02-24 12:54:45
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random

def generate(level=1, **kwargs):
    def f(n):
        return f"({n})" if n < 0 else str(n)
    def gd():
        v_div = random.choice([i for i in range(-12, 13) if i != 0])
        v_q = random.randint(-10, 10)
        return v_div * v_q, v_div, v_q
    t = random.randint(1, 3)
    if t == 1:
        v_s, v_c, v_q = gd()
        v_a = random.randint(-25, 25)
        v_b = v_s - v_a
        v_d = random.randint(-10, 10)
        v_e, v_f, v_g = random.randint(-10, 10), random.randint(-10, 10), random.randint(-25, 25)
        v_op = random.choice(['+', '-'])
        txt = f"[{f(v_a)}+{f(v_b)}]÷{f(v_c)}×{f(v_d)}{v_op}|{f(v_e)}×{f(v_f)}+{f(v_g)}|"
        ans = v_q * v_d + (abs(v_e * v_f + v_g) if v_op == '+' else -abs(v_e * v_f + v_g))
    elif t == 2:
        v_a, v_b, v_c = random.randint(-10, 10), random.randint(-20, 20), random.randint(-20, 20)
        v_s, v_e, v_q = gd()
        v_f, v_g = random.randint(-20, 20), random.randint(-20, 20)
        txt = f"{f(v_a)}×({f(v_b)}-{f(v_c)})+{f(v_s)}÷{f(v_e)}-|{f(v_f)}+{f(v_g)}|"
        ans = v_a * (v_b - v_c) + v_q - abs(v_f + v_g)
    else:
        v_a, v_b, v_c = random.randint(-20, 20), random.randint(-20, 20), random.randint(-10, 10)
        v_s, v_f, v_q = gd()
        v_d = random.randint(-25, 25)
        v_e = v_s - v_d
        txt = f"|{f(v_a)}-{f(v_b)}|×{f(v_c)}+({f(v_d)}+{f(v_e)})÷{f(v_f)}"
        ans = abs(v_a - v_b) * v_c + v_q
    return {
        'question_text': f"計算 {txt} 的值。",
        'answer': '',
        'correct_answer': str(int(ans)),
        'mode': 1
    }

def check(user_answer, correct_answer):
    res = str(user_answer).strip() == str(correct_answer).strip()
    return {
        'correct': res,
        'result': '正確' if res else '錯誤'
    }