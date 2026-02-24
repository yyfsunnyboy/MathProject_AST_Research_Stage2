# ==============================================================================
# ID: jh_數學2上_FourOperationsOfRadicals
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 86.86s | Tokens: In=753, Out=1338
# Created At: 2026-02-20 02:55:58
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
import math

def generate(level=1, **kwargs):
    ops = ['+', '-', '*', '/']
    terms = []
    for _ in range(2 if level == 1 else 3):
        coeff = random.randint(1, 5)
        radicand = random.choice([2,3,5,6,7,8,10,12,15,18,20,24,27,30])
        terms.append(f"{coeff}\\sqrt{{{radicand}}}")
    expr1 = " + ".join(terms)
    terms2 = []
    for _ in range(2 if level == 1 else 3):
        coeff = random.randint(1, 5)
        radicand = random.choice([2,3,5,6,7,8,10,12,15,18,20,24,27,30])
        terms2.append(f"{coeff}\\sqrt{{{radicand}}}")
    expr2 = " + ".join(terms2)
    op = random.choice(ops)
    question = f"化簡 $({expr1}) {op} ({expr2})$"
    return {
        'question_text': question,
        'answer': '',
        'correct_answer': simplify(expr1, expr2, op),
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}

def simplify(expr1, expr2, op):
    def parse(expr):
        terms = []
        parts = expr.split('+')
        for p in parts:
            if 'sqrt' in p:
                coeff = 1
                if p[0].isdigit():
                    coeff = int(p.split('sqrt')[0])
                    p = p.split('sqrt')[1]
                radicand = int(p.strip('{}'))
                terms.append((coeff, radicand))
        return terms
    
    def combine(terms1, terms2, op):
        if op == '+':
            return terms1 + terms2
        elif op == '-':
            return terms1 + [(-coeff, rad) for coeff, rad in terms2]
        elif op == '*':
            res = []
            for c1, r1 in terms1:
                for c2, r2 in terms2:
                    res.append((c1*c2, r1*r2))
            return res
        elif op == '/':
            return [(c1/c2, r1 - r2) for c1, r1 in terms1 for c2, r2 in terms2]
    
    terms1 = parse(expr1)
    terms2 = parse(expr2)
    combined = combine(terms1, terms2, op)
    
    from collections import defaultdict
    grouped = defaultdict(float)
    for coeff, rad in combined:
        grouped[rad] += coeff
    
    result = []
    for rad, coeff in grouped.items():
        if coeff != 0:
            if coeff == 1:
                result.append(f"\\sqrt{{{rad}}}")
            elif coeff == -1:
                result.append(f"-\\sqrt{{{rad}}}")
            else:
                result.append(f"{coeff}\\sqrt{{{rad}}}")
    
    return " + ".join(result) if result else "0"