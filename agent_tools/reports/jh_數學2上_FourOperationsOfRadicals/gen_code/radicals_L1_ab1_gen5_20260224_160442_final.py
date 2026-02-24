# ==============================================================================
# ID: jh_數學2上_FourOperationsOfRadicals
# Model: qwen3-8b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 12.60s | Tokens: In=637, Out=909
# Created At: 2026-02-24 16:04:42
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
import math

def generate(level=1, **kwargs):
    if level == 1:
        a = random.randint(1, 5)
        b = random.randint(1, 5)
        c = random.randint(1, 5)
        d = random.randint(1, 5)
        e = random.randint(1, 5)
        f = random.randint(1, 5)
        g = random.randint(1, 5)
        h = random.randint(1, 5)
        i = random.randint(1, 5)
        j = random.randint(1, 5)
        k = random.randint(1, 5)
        l = random.randint(1, 5)
        m = random.randint(1, 5)
        n = random.randint(1, 5)
        o = random.randint(1, 5)
        p = random.randint(1, 5)
        q = random.randint(1, 5)
        r = random.randint(1, 5)
        s = random.randint(1, 5)
        t = random.randint(1, 5)
        u = random.randint(1, 5)
        v = random.randint(1, 5)
        w = random.randint(1, 5)
        x = random.randint(1, 5)
        y = random.randint(1, 5)
        z = random.randint(1, 5)
        return {
            'question_text': f'\\left(\\sqrt{{{a}}} + \\sqrt{{{b}}} - {c}\\sqrt{{{d}}}\\right) + \\left(\\sqrt{{{e}}} + \\sqrt{{{f}}}\\right)\\left(\\sqrt{{{g}}} - {h}\\right)',
            'answer': '',
            'correct_answer': '',
            'mode': 1
        }
    elif level == 2:
        a = random.randint(1, 5)
        b = random.randint(1, 5)
        c = random.randint(1, 5)
        d = random.randint(1, 5)
        e = random.randint(1, 5)
        f = random.randint(1, 5)
        g = random.randint(1, 5)
        h = random.randint(1, 5)
        i = random.randint(1, 5)
        j = random.randint(1, 5)
        k = random.randint(1, 5)
        l = random.randint(1, 5)
        m = random.randint(1, 5)
        n = random.randint(1, 5)
        o = random.randint(1, 5)
        p = random.randint(1, 5)
        q = random.randint(1, 5)
        r = random.randint(1, 5)
        s = random.randint(1, 5)
        t = random.randint(1, 5)
        u = random.randint(1, 5)
        v = random.randint(1, 5)
        w = random.randint(1, 5)
        x = random.randint(1, 5)
        y = random.randint(1, 5)
        z = random.randint(1, 5)
        return {
            'question_text': f'\\left(\\sqrt{{{a}}} + \\sqrt{{{b}}} - {c}\\sqrt{{{d}}}\\right) + \\left(\\sqrt{{{e}}} + \\sqrt{{{f}}}\\right)\\left(\\sqrt{{{g}}} - {h}\\right)',
            'answer': '',
            'correct_answer': '',
            'mode': 1
        }
    else:
        return {
            'question_text': f'\\left(\\sqrt{{{a}}} + \\sqrt{{{b}}} - {c}\\sqrt{{{d}}}\\right) + \\left(\\sqrt{{{e}}} + \\sqrt{{{f}}}\\right)\\left(\\sqrt{{{g}}} - {h}\\right)',
            'answer': '',
            'correct_answer': '',
            'mode': 1
        }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': 'Correct' if correct else 'Wrong'}