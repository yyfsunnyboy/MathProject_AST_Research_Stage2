# ==============================================================================
# ID: jh_數學2上_FourOperationsOfRadicals
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 45.19s | Tokens: In=753, Out=1314
# Created At: 2026-02-20 03:29:06
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
import math

def generate(level=1, **kwargs):
    ops = ['+', '-', '*', '/']
    terms = []
    for _ in range(2 if level == 1 else 3):
        a = random.randint(2, 50)
        b = random.randint(2, 50)
        terms.append(f"\\sqrt{{{a}}}")
        terms.append(f"\\sqrt{{{b}}}")
    expr = []
    for i in range(len(terms)-1):
        expr.append(terms[i])
        expr.append(random.choice(ops))
    expr.append(terms[-1])
    question = "$" + " ".join(expr) + "$"
    answer = simplify(expr)
    return {
        'question_text': f"化簡 {question}",
        'answer': '',
        'correct_answer': answer,
        'mode': 1
    }

def simplify(expr):
    def sqrt_val(s):
        return int(s.split('{')[1].split('}')[0])
    
    def combine_terms(terms):
        groups = {}
        for t in terms:
            val = sqrt_val(t)
            if val in groups:
                groups[val] += 1
            else:
                groups[val] = 1
        result = []
        for k in sorted(groups):
            if groups[k] == 1:
                result.append(f"\\sqrt{{{k}}}")
            else:
                result.append(f"{groups[k]}\\sqrt{{{k}}}")
        return " + ".join(result)
    
    terms = expr.split()
    new_terms = []
    i = 0
    while i < len(terms):
        if terms[i] in ['+', '-']:
            new_terms.append(terms[i])
            i += 1
        else:
            new_terms.append(terms[i])
            i += 1
    return combine_terms(new_terms)

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}