# ==============================================================================
# ID: jh_數學2上_FourOperationsOfRadicals
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 36.21s | Tokens: In=753, Out=1054
# Created At: 2026-02-20 03:43:16
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
import math

def generate(level=1, **kwargs):
    ops = ['+', '-', '*', '/']
    terms = []
    for _ in range(random.randint(2,4)):
        a = random.randint(1, 20)
        b = random.randint(1, 20)
        op = random.choice(ops)
        if op == '+':
            terms.append(f"\\sqrt{{{a}}} + \\sqrt{{{b}}}")
        elif op == '-':
            terms.append(f"\\sqrt{{{a}}} - \\sqrt{{{b}}}")
        elif op == '*':
            terms.append(f"(\\sqrt{{{a}}} + \\sqrt{{{b}}})(\\sqrt{{{a}}} - \\sqrt{{{b}}})")
        else:
            terms.append(f"\\frac{{\\sqrt{{{a}}}}}{{\\sqrt{{{b}}}}}")
    
    expr = " + ".join(terms)
    correct = eval(expr.replace('sqrt', 'math.sqrt'))
    simplified = simplify(correct)
    return {
        'question_text': f"化簡 ${expr}$",
        'answer': '',
        'correct_answer': simplified,
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}

def simplify(expr):
    if isinstance(expr, (int, float)):
        return f"{expr}"
    if isinstance(expr, tuple):
        return simplify(expr[0]) + " + " + simplify(expr[1])
    if isinstance(expr, list):
        return " + ".join([simplify(x) for x in expr])
    return f"{expr}"