# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: qwen3-8b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 186.96s | Tokens: In=598, Out=11842
# Created At: 2026-02-14 08:32:10
# Fix Status: [No Healer - Bare LLM Output] | Fixes: Basic=0, Advanced=None
# Verification: Internal Logic Check = PASSED
# ==============================================================================

import random

def generate(level=1, **kwargs):
    if level == 1:
        a = random.randint(-100, 100)
        b = random.randint(-100, 100)
        c = random.randint(-100, 100)
        while c == 0:
            c = random.randint(-100, 100)
        d = random.randint(-100, 100)
        e = random.randint(-100, 100)
        f = random.randint(-100, 100)
        while f == 0:
            f = random.randint(-100, 100)
        g = random.randint(-100, 100)
        left_part = f"({a} + {b}) ÷ {c} × {d}"
        right_part = f"{e} - {f} × {g}"
        question_text = f"{left_part} + {right_part}"
        question_text = question_text.replace('÷', '/').replace('×', '*')
        correct_answer = str(eval(question_text))
    elif level == 2:
        a = random.randint(-100, 100)
        b = random.randint(-100, 100)
        c = random.randint(-100, 100)
        left_part = f"|{a} × {b} - {c}|"
        d = random.randint(-100, 100)
        e = random.randint(-100, 100)
        f = random.randint(-100, 100)
        while f == 0:
            f = random.randint(-100, 100)
        g = random.randint(-100, 100)
        right_part = f"({d} + {e}) ÷ {f} × {g}"
        question_text = f"{left_part} - {right_part}"
        question_text = question_text.replace('÷', '/').replace('×', '*')
        correct_answer = str(eval(question_text))
    else:
        correct_answer = ''
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    user_answer = user_answer.strip()
    correct_answer = correct_answer.strip()
    return {
        'correct': user_answer == correct_answer,
        'result': '正確' if user_answer == correct_answer else '錯誤'
}