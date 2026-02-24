import random

def generate(level=1, **kwargs):
    ops = ['+', '-', '*', '/']
    op = random.choice(ops)
    poly1 = generate_poly(level)
    poly2 = generate_poly(level)
    
    if op == '+':
        result = add_polynomials(poly1, poly2)
    elif op == '-':
        result = subtract_polynomials(poly1, poly2)
    elif op == '*':
        result = multiply_polynomials(poly1, poly2)
    else:
        result = divide_polynomials(poly1, poly2)
    
    question = f"計算 ${poly1}$ {op} ${poly2}$"
    return {
        'question_text': question,
        'answer': '',
        'correct_answer': format_polynomial(result),
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}

def generate_poly(level):
    terms = []
    max_terms = 3 if level == 1 else 4
    max_degree = 3 if level == 1 else 5
    max_coeff = 5 if level == 1 else 10
    
    for _ in range(random.randint(1, max_terms)):
        coeff = random.randint(-max_coeff, max_coeff)
        if coeff == 0:
            continue
        degree = random.randint(0, max_degree)
        terms.append((coeff, degree))
    
    return format_polynomial(terms)

def add_polynomials(p1, p2):
    return combine_polynomials(p1, p2, lambda a, b: a + b)

def subtract_polynomials(p1, p2):
    return combine_polynomials(p1, p2, lambda a, b: a - b)

def multiply_polynomials(p1, p2):
    result = {}
    for (c1, d1) in p1:
        for (c2, d2) in p2:
            coeff = c1 * c2
            degree = d1 + d2
            result[degree] = result.get(degree, 0) + coeff
    return list(result.items())

def divide_polynomials(p1, p2):
    p1 = dict(p1)
    p2 = dict(p2)
    if not p2:
        return []
    
    max_deg_p1 = max(p1.keys()) if p1 else 0
    max_deg_p2 = max(p2.keys()) if p2 else 0
    
    if max_deg_p1 < max_deg_p2:
        return []
    
    result = {}
    while max_deg_p1 >= max_deg_p2:
        deg_diff = max_deg_p1 - max_deg_p2
        coeff = p1[max_deg_p1] // p2[max_deg_p2]
        result[deg_diff] = coeff
        for d in p2:
            p1[d] = p1.get(d, 0) - coeff * p2[d]
        max_deg_p1 = max(p1.keys()) if p1 else 0
    
    return list(result.items())

def combine_polynomials(p1, p2, func):
    result = {}
    for (c, d) in p1 + p2: