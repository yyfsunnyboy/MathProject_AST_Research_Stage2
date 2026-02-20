# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: qwen3-8b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 119.47s | Tokens: In=502, Out=7978
# Created At: 2026-02-20 09:50:39
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random

def generate(level=1, **kwargs):
    a = random.randint(-20, 20)
    b = random.randint(-20, 20)
    op = random.choice(['+', '-'])
    if op == '+':
        step1 = a + b
    else:
        step1 = a - b
    possible_c = []
    for c in range(-10, 11):
        if c != 0 and step1 % c == 0:
            possible_c.append(c)
    if not possible_c:
        c = random.choice([1, -1])
    else:
        c = random.choice(possible_c)
    d = random.randint(-10, 10)
    e = random.randint(-30, 30)
    f = random.randint(-30, 30)
    g = random.randint(-30, 30)
    a_str = f"{a}" if a >= 0 else f"({a})"
    b_str = f"{b}" if b >= 0 else f"({b})"
    e_str = f"{e}" if e >= 0 else f"({e})"
    f_str = f"{f}" if f >= 0 else f"({f})"
    g_str = f"{g}" if g >= 0 else f"({g})"
    question_text = f"[{a_str}{op}{b_str}] ÷ {c} × {d} + |{e_str} × {f_str} - {g_str}|"
    step2 = step1 // c
    step3 = step2 * d
    abs_part = abs(e * f - g)
    correct_answer = str(step3 + abs_part)
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        user_int = int(user_answer)
        correct_int = int(correct_answer)
        return {
            'correct': user_int == correct_int,
            'result': '正確' if user_int == correct_int else '錯誤'
        }
    except:
        return {
            'correct': False,
            'result': '錯誤'
        }