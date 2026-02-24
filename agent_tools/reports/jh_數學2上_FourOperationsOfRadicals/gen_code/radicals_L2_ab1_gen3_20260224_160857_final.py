# ==============================================================================
# ID: jh_數學2上_FourOperationsOfRadicals
# Model: qwen3-8b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 11.09s | Tokens: In=637, Out=801
# Created At: 2026-02-24 16:08:57
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
import math

def generate(level=1, **kwargs):
    if level == 1:
        a = random.randint(1, 10)
        b = random.randint(1, 10)
        c = random.randint(1, 10)
        d = random.randint(1, 10)
        e = random.randint(1, 10)
        f = random.randint(1, 10)
        g = random.randint(1, 10)
        h = random.randint(1, 10)
        i = random.randint(1, 10)
        j = random.randint(1, 10)
        k = random.randint(1, 10)
        l = random.randint(1, 10)
        m = random.randint(1, 10)
        n = random.randint(1, 10)
        o = random.randint(1, 10)
        p = random.randint(1, 10)
        q = random.randint(1, 10)
        r = random.randint(1, 10)
        s = random.randint(1, 10)
        t = random.randint(1, 10)
        u = random.randint(1, 10)
        v = random.randint(1, 10)
        w = random.randint(1, 10)
        x = random.randint(1, 10)
        y = random.randint(1, 10)
        z = random.randint(1, 10)
        term1 = f"\\sqrt{{{a * 2}}} + \\sqrt{{{b * 2}}} - {c}\\sqrt{{{d * 2}}}"
        term2 = f"\\sqrt{{{e}} + \\sqrt{{{f}}}}\\sqrt{{{g}} - {h}}"
        term3 = f"\\sqrt{{{i}} + \\sqrt{{{j}}}}\\sqrt{{{k}} - {l}}"
        term4 = f"\\sqrt{{{m}} + \\sqrt{{{n}}}}\\sqrt{{{o}} - {p}}"
        term5 = f"\\sqrt{{{q}} + \\sqrt{{{r}}}}\\sqrt{{{s}} - {t}}"
        term6 = f"\\sqrt{{{u}} + \\sqrt{{{v}}}}\\sqrt{{{w}} - {x}}"
        term7 = f"\\sqrt{{{y}} + \\sqrt{{{z}}}}\\sqrt{{{a}} - {b}}"
        question_text = f"Simplify ({term1}) + ({term2}) + ({term3}) + ({term4}) + ({term5}) + ({term6}) + ({term7})"
        answer = f"\\frac{{{a + b - c * d + e + f + g - h + i + j + k - l + m + n + o - p + q + r + s - t + u + v + w - x + y + z}}}{{{a + b - c * d + e + f + g - h + i + j + k - l + m + n + o - p + q + r + s - t + u + v + w - x + y + z}}}"
        return {
            'question_text': question_text,
            'answer': answer,
            'correct_answer': answer,
            'mode': 1
        }
    else:
        return {
            'question_text': 'Error: Level not supported',
            'answer': '',
            'correct_answer': '',
            'mode': 1
        }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': 'Correct' if correct else 'Wrong'}