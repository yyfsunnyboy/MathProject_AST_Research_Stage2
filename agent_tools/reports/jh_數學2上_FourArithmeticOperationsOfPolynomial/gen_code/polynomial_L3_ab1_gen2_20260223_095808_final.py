# ==============================================================================
# ID: jh_數學2上_FourArithmeticOperationsOfPolynomial
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 70.81s | Tokens: In=717, Out=2048
# Created At: 2026-02-23 09:58:08
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random

def generate(level=1, **kwargs):
    modes = ['add', 'subtract', 'multiply']
    mode = random.choice(modes)
    poly1 = generate_polynomial(level)
    poly2 = generate_polynomial(level)
    
    if mode == 'add':
        result = add_polynomials(poly1, poly2)
        question = f"計算 ${polynomial_to_latex(poly1)} + {polynomial_to_latex(poly2)}$"
    elif mode == 'subtract':
        result = subtract_polynomials(poly1, poly2)
        question = f"計算 ${polynomial_to_latex(poly1)} - {polynomial_to_latex(poly2)}$"
    else:
        result = multiply_polynomials(poly1, poly2)
        question = f"展開並化簡 ${polynomial_to_latex(poly1)} \\cdot {polynomial_to_latex(poly2)}$"
    
    correct_answer = polynomial_to_string(result)
    return {
        'question_text': question,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}

def generate_polynomial(level):
    terms = []
    max_degree = 2 + level
    max_terms = 3 + level
    for _ in range(random.randint(1, max_terms)):
        degree = random.randint(0, max_degree)
        coeff = random.randint(-10 + level*5, 10 - level*5)
        if coeff == 0:
            continue
        terms.append((degree, coeff))
    return dict(terms)

def add_polynomials(p1, p2):
    result = {}
    for deg in set(p1.keys()).union(p2.keys()):
        result[deg] = p1.get(deg, 0) + p2.get(deg, 0)
    return {k: v for k, v in result.items() if v != 0}

def subtract_polynomials(p1, p2):
    result = {}
    for deg in set(p1.keys()).union(p2.keys()):
        result[deg] = p1.get(deg, 0) - p2.get(deg, 0)
    return {k: v for k, v in result.items() if v != 0}

def multiply_polynomials(p1, p2):
    result = {}
    for deg1, coeff1 in p1.items():
        for deg2, coeff2 in p2.items():
            deg = deg1 + deg2
            result[deg] = result.get(deg, 0) + coeff1 * coeff2
    return {k: v for k, v in result.items() if v != 0}

def polynomial_to_latex(poly):
    terms = []
    for deg in sorted(poly.keys(), reverse=True):
        coeff = poly[deg]
        if coeff == 1 and deg != 0:
            terms.append(f"x^{deg}" if deg > 1 else "x")
        elif coeff == -1 and deg != 0:
            terms.append(f"-x^{deg}" if deg > 1 else "-x")
        else:
            if deg == 0:
                terms.append(f"{coeff}")
            else:
                terms.append(f"{coeff}x^{deg}" if deg > 1 else f"{coeff}x")
    return " + ".join(terms).replace("+ -", "-")

def polynomial_to_string(poly):
    terms = []
    for deg in sorted(poly.keys(), reverse=True):
        coeff = poly[deg]
        if coeff == 1 and deg != 0:
            terms.append(f"x^{deg}" if deg > 1 else "