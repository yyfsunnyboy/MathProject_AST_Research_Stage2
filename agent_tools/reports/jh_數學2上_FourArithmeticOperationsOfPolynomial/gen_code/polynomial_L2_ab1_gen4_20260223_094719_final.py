# ==============================================================================
# ID: jh_數學2上_FourArithmeticOperationsOfPolynomial
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 70.79s | Tokens: In=717, Out=2048
# Created At: 2026-02-23 09:47:19
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random

def generate(level=1, **kwargs):
    ops = ['+', '-', '*', '/']
    op = random.choice(ops)
    poly1 = generate_polynomial(level)
    poly2 = generate_polynomial(level)
    
    if op == '+':
        result = add_polynomials(poly1, poly2)
    elif op == '-':
        result = subtract_polynomials(poly1, poly2)
    elif op == '*':
        result = multiply_polynomials(poly1, poly2)
    else:
        result = divide_polynomials(poly1, poly2)
    
    question = f"計算 ${format_polynomial(poly1)} {op} {format_polynomial(poly2)}$"
    return {
        'question_text': question,
        'answer': '',
        'correct_answer': format_polynomial(result),
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}

def generate_polynomial(level):
    terms = []
    max_degree = 2 + level
    max_coeff = 5 + level * 2
    
    for _ in range(random.randint(2, 3)):
        degree = random.randint(1, max_degree)
        coeff = random.randint(-max_coeff, max_coeff)
        if coeff == 0:
            continue
        terms.append((coeff, degree))
    
    terms.sort(key=lambda x: -x[1])
    return terms

def add_polynomials(p1, p2):
    result = {}
    for coeff, deg in p1 + p2:
        result[deg] = result.get(deg, 0) + coeff
    return [(v, k) for k, v in result.items()]

def subtract_polynomials(p1, p2):
    result = {}
    for coeff, deg in p1 + [( -coeff, deg) for coeff, deg in p2]:
        result[deg] = result.get(deg, 0) + coeff
    return [(v, k) for k, v in result.items()]

def multiply_polynomials(p1, p2):
    result = {}
    for c1, d1 in p1:
        for c2, d2 in p2:
            deg = d1 + d2
            coeff = c1 * c2
            result[deg] = result.get(deg, 0) + coeff
    return [(v, k) for k, v in result.items()]

def divide_polynomials(p1, p2):
    if not p2:
        return []
    result = {}
    p1 = dict(p1)
    p2 = dict(p2)
    
    while p1:
        max_deg = max(p1.keys())
        max_deg2 = max(p2.keys())
        if max_deg < max_deg2:
            return []
        quotient = p1[max_deg] // p2[max_deg2]
        deg = max_deg - max_deg2
        result[deg] = result.get(deg, 0) + quotient
        
        for d in p2:
            p1[d] =