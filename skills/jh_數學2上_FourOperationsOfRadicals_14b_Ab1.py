# ==============================================================================
# ID: jh_數學2上_FourOperationsOfRadicals
# Model: qwen3-14b-nothink:latest | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 385.04s | Tokens: In=735, Out=8775
# Created At: 2026-02-15 18:25:36
# Fix Status: [Clean Pass] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PASSED
# ==============================================================================
import random
import math

def simplify_radical(n):
    max_square = 1
    i = 2
    while i * i <= n:
        count = 0
        while n % i == 0:
            count += 1
            n = n // i
        if count % 2 == 0:
            max_square *= i ** count
        else:
            max_square *= i ** (count - 1)
        i += 1
    if n > 1:
        max_square *= n
    sqrt_max = int(math.sqrt(max_square))
    remaining = n // max_square
    if remaining == 1:
        return f"{sqrt_max}"
    else:
        return f"{sqrt_max} \\sqrt{{{remaining}}}"

def generate(level=1, **kwargs):
    op = random.choice(['+', '-', '*', '/'])
    if op in ['+', '-']:
        a = random.randint(1, 5)
        b = random.randint(2, 20)
        c = random.randint(1, 5)
        d = random.randint(2, 20)
        if random.random() < 0.5:
            d = b
        question = f"({a} \\sqrt{{{b}}} {op} {c} \\sqrt{{{d}}})"
        if b == d:
            coeff = a + c if op == '+' else a - c
            correct_answer = f"{coeff} \\sqrt{{{b}}}"
        else:
            correct_answer = f"{a} \\sqrt{{{b}}} {op} {c} \\sqrt{{{d}}}"
    elif op == '*':
        a = random.randint(2, 20)
        b = random.randint(2, 20)
        c = random.randint(2, 20)
        d = random.randint(2, 20)
        question = f"( \\sqrt{{{a}}} + \\sqrt{{{b}}} )( \\sqrt{{{c}}} - \\sqrt{{{d}}} )"
        term1 = f"\\sqrt{{{a*c}}}"
        term2 = f"-\\sqrt{{{a*d}}}"
        term3 = f"+\\sqrt{{{b*c}}}"
        term4 = f"-\\sqrt{{{b*d}}}"
        correct_answer = f"{term1} {term2} {term3} {term4}"
    elif op == '/':
        a = random.randint(1, 5)
        b = random.randint(2, 20)
        c = random.randint(1, 5)
        d = random.randint(2, 20)
        e = random.randint(2, 20)
        question = f"({a} \\sqrt{{{b}}} + {c} \\sqrt{{{d}}}) ÷ \\sqrt{{{e}}}"
        term1 = f"{a} \\sqrt{{{b*e}}}"
        term2 = f"+ {c} \\sqrt{{{d*e}}}"
        term1_simplified = simplify_radical(b*e)
        term2_simplified = simplify_radical(d*e)
        numerator = f"{a} {term1_simplified} + {c} {term2_simplified}"
        correct_answer = f"\\frac{{{numerator}}}{{{e}}}"
    return {
        'question_text': question,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    return {
        'correct': user_answer.strip() == correct_answer.strip(),
        'result': '正確' if user_answer.strip() == correct_answer.strip() else '錯誤'
    }