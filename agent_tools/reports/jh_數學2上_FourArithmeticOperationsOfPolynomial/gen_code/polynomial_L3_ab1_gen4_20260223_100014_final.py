# ==============================================================================
# ID: jh_數學2上_FourArithmeticOperationsOfPolynomial
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 56.27s | Tokens: In=717, Out=1633
# Created At: 2026-02-23 10:00:14
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random

def generate(level=1, **kwargs):
    modes = ['add', 'subtract', 'multiply']
    mode = random.choice(modes)
    poly1 = generate_polynomial()
    poly2 = generate_polynomial()
    
    if mode == 'add':
        question = f"計算 ${poly1} + {poly2}$"
        answer = add_polynomials(poly1, poly2)
    elif mode == 'subtract':
        question = f"計算 ${poly1} - {poly2}$"
        answer = subtract_polynomials(poly1, poly2)
    else:
        question = f"展開並化簡 ${poly1} \\times {poly2}$"
        answer = multiply_polynomials(poly1, poly2)
    
    return {
        'question_text': question,
        'answer': '',
        'correct_answer': answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}

def generate_polynomial():
    terms = []
    degrees = sorted(random.sample(range(3), 2), reverse=True)
    
    for deg in degrees:
        coeff = random.randint(-5, 5)
        if coeff == 0:
            continue
        if deg == 0:
            terms.append(f"{coeff}")
        elif deg == 1:
            terms.append(f"{coeff}x")
        else:
            terms.append(f"{coeff}x^{deg}")
    
    if not terms:
        terms.append("0")
    
    return " + ".join(terms).replace("+ -", "-")

def add_polynomials(p1, p2):
    return simplify_polynomial(f"({p1}) + ({p2})")

def subtract_polynomials(p1, p2):
    return simplify_polynomial(f"({p1}) - ({p2})")

def multiply_polynomials(p1, p2):
    return simplify_polynomial(f"({p1}) * ({p2})")

def simplify_polynomial(expr):
    terms = []
    expr = expr.replace(" ", "").replace("+", " +").replace("-", " -").split()
    
    for term in expr:
        if term == "+" or term == "-":
            continue
        if "x^" in term:
            parts = term.split("x^")
            coeff = parts[0]
            deg = parts[1]
            terms.append((int(coeff), int(deg)))
        elif "x" in term:
            parts = term.split("x")
            coeff = parts[0]
            terms.append((int(coeff), 1))
        else:
            terms.append((int(term), 0))
    
    merged = {}
    for coeff, deg in terms:
        if deg in merged:
            merged[deg] += coeff
        else:
            merged[deg] = coeff
    
    sorted_deg = sorted(merged.keys(), reverse=True)
    result = []
    
    for deg in sorted_deg:
        coeff = merged[deg]
        if coeff == 0:
            continue
        if deg == 0:
            result.append(f"{coeff}")
        elif deg == 1:
            result.append(f"{coeff}x")
        else:
            result.append(f"{coeff}x^{deg}")
    
    return "+".join(result).replace("+-", "-")