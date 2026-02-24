# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: gemini-3-flash | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 51.42s | Tokens: In=460, Out=457
# Created At: 2026-02-22 23:58:32
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random

def generate(level=1, **kwargs):
    c = random.choice([i for i in range(-12, 13) if i != 0])
    k = random.randint(-10, 10)
    a = random.randint(-30, 30)
    b = c * k - a
    d = random.randint(-10, 10)
    e = random.randint(-10, 10)
    f = random.randint(-10, 10)
    g = random.randint(-20, 20)
    ans = (k * d) + abs(e * f + g)
    def p(n):
        return f"({n})" if n < 0 else str(n)
    s_a, s_b, s_c, s_d = p(a), p(b), p(c), p(d)
    s_e, s_f, s_g = p(e), p(f), p(g)
    q1 = f"[{s_a}+{s_b}]"
    q2 = f"÷{s_c}×{s_d}"
    q3 = f"|{s_e}×{s_f}+{s_g}|"
    txt = f"計算 {q1}{q2}+{q3} 的值。"
    txt = txt.replace("+-", "-").replace("-+", "-").replace("++", "+").replace("--", "+")
    return {
        'question_text': txt,
        'answer': '',
        'correct_answer': str(ans),
        'mode': 1
    }

def check(user_answer, correct_answer):
    is_correct = str(user_answer).strip() == str(correct_answer).strip()
    return {
        'correct': is_correct,
        'result': '正確' if is_correct else '錯誤'
    }