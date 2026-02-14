# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 301.22s | Tokens: In=622, Out=8401
# Created At: 2026-02-14 01:17:00
# Fix Status: [No Healer - Bare LLM Output] | Fixes: Basic=0, Advanced=None
# Verification: Internal Logic Check = PASSED
# ==============================================================================

import random
import re

def generate(level=1, **kwargs):
    if level == 1:
        max_val = 20
    else:
        max_val = 50

    templates = [
        "[({a}+{b})]÷{c}×{d}+|{e}×{f}-{g}|",
        "|{a}+{b}|÷({c}-{d})×{e}+{f}",
        "({a}×{b}-{c})÷|{d}+{e}|+{f}×{g}"
    ]
    template = random.choice(templates)

    if template == templates[0]:
        a = random.randint(-max_val, max_val)
        b = random.randint(-max_val, max_val)
        c = random.randint(-max_val, max_val)
        while c == 0:
            c = random.randint(-max_val, max_val)
        d = random.randint(-max_val, max_val)
        e = random.randint(-max_val, max_val)
        f = random.randint(-max_val, max_val)
        g = random.randint(-max_val, max_val)
        expr = template.format(a=a, b=b, c=c, d=d, e=e, f=f, g=g)
    elif template == templates[1]:
        a = random.randint(-max_val, max_val)
        b = random.randint(-max_val, max_val)
        c = random.randint(-max_val, max_val)
        d = random.randint(-max_val, max_val)
        while c - d == 0:
            d = random.randint(-max_val, max_val)
        e = random.randint(-max_val, max_val)
        f = random.randint(-max_val, max_val)
        expr = template.format(a=a, b=b, c=c, d=d, e=e, f=f)
    elif template == templates[2]:
        a = random.randint(-max_val, max_val)
        b = random.randint(-max_val, max_val)
        c = random.randint(-max_val, max_val)
        d = random.randint(-max_val, max_val)
        e = random.randint(-max_val, max_val)
        while d + e == 0:
            e = random.randint(-max_val, max_val)
        f = random.randint(-max_val, max_val)
        g = random.randint(-max_val, max_val)
        expr = template.format(a=a, b=b, c=c, d=d, e=e, f=f, g=g)

    expr = expr.replace('÷', '/').replace('×', '*')
    expr = re.sub(r'\|([^|]+)\|', r'abs(\1)', expr)

    try:
        correct_answer = eval(expr)
    except:
        correct_answer = 0

    question_text = expr.replace('/', '÷').replace('*', '×')
    question_text = re.sub(r'abs\(([^)]+)\)', r'|\1|', question_text)
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': str(correct_answer),
        'mode': 1
    }

def check(user_answer, correct_answer):
    return {
        'correct': user_answer == correct_answer,
        'result': '正確' if user_answer == correct_answer else '錯誤'
}