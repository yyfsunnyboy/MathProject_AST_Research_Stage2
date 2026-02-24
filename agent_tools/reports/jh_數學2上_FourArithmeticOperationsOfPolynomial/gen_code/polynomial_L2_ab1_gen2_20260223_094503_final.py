# ==============================================================================
# ID: jh_數學2上_FourArithmeticOperationsOfPolynomial
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 52.07s | Tokens: In=717, Out=1510
# Created At: 2026-02-23 09:45:03
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random

def generate(level=1, **kwargs):
    ops = ['+', '-', '*']
    op = random.choice(ops)
    poly1 = generate_poly(level)
    poly2 = generate_poly(level)
    
    if op == '+':
        correct = add_polynomials(poly1, poly2)
    elif op == '-':
        correct = subtract_polynomials(poly1, poly2)
    else:
        correct = multiply_polynomials(poly1, poly2)
    
    question = f"計算 ${poly1}$ {op} ${poly2}$"
    return {
        'question_text': question,
        'answer': '',
        'correct_answer': correct,
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}

def generate_poly(level):
    terms = []
    max_degree = 2 + level
    num_terms = random.randint(2, 3 + level)
    
    for _ in range(num_terms):
        coeff = random.randint(1, 5) * (-1 if random.random() > 0.5 else 1)
        degree = random.randint(0, max_degree)
        
        if degree == 0:
            terms.append(f"{coeff}")
        else:
            terms.append(f"{coeff}x^{degree}" if coeff != 1 else f"x^{degree}" if coeff == 1 else f"-x^{degree}")
    
    return " + ".join(terms).replace("+ -", "-")

def add_polynomials(p1, p2):
    return combine_terms(p1 + " + " + p2)

def subtract_polynomials(p1, p2):
    return combine_terms(p1 + " - " + p2)

def multiply_polynomials(p1, p2):
    terms = []
    p1_terms = p1.split(" + ")
    p2_terms = p2.split(" + ")
    
    for t1 in p1_terms:
        for t2 in p2_terms:
            terms.append(multiply_terms(t1, t2))
    
    return combine_terms(" + ".join(terms))

def multiply_terms(t1, t2):
    coeff1, exp1 = parse_term(t1)
    coeff2, exp2 = parse_term(t2)
    return f"{coeff1*coeff2}x^{exp1+exp2}" if coeff1*coeff2 != 1 else f"x^{exp1+exp2}"

def parse_term(term):
    if 'x' not in term:
        return (int(term), 0)
    parts = term.split('x^') if 'x^' in term else term.split('x')
    coeff = int(parts[0]) if parts[0] != '' else 1
    exp = int(parts[1]) if len(parts) > 1 else 1
    return (coeff, exp)

def combine_terms(expr):
    terms = expr.split(" + ")
    coeff_dict = {}
    
    for term in terms:
        if 'x' in term:
            parts = term.split('x^') if 'x^' in term else term.split('x')
            coeff = int(parts[0]) if parts[0] != '' else 1
            exp = int(parts[1]) if len(parts) > 1 else 1
            coeff_dict[exp] = coeff_dict.get(exp, 0) + coeff
        else:
            coeff_dict[0] = coeff_dict.get(0, 0) + int(term)
    
    sorted_terms = sorted(coeff_dict.items(), key=lambda x: x[0], reverse=True)
    result = []
    
    for exp, coeff in sorted_terms:
        if exp == 0:
            result.append(f"{coeff}")
        elif exp == 1:
            if coeff == 1:
                result.append("x")
            elif coeff == -1:
                result.append("-x")
            else:
                result.append(f"{coeff}x")
        else:
            if coeff == 1:
                result.append(f"x^{exp}")
            elif coeff == -1:
                result.append(f"-x^{exp}")
            else:
                result.append(f"{coeff}x^{exp}")
    
    return " + ".join(result).replace("+ -", "-")