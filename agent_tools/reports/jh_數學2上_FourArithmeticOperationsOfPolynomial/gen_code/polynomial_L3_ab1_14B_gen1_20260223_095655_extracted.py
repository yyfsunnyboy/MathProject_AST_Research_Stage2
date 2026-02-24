import random

def generate(level=1, **kwargs):
    ops = ['+', '-', '*', '/']
    op = random.choice(ops)
    poly1 = generate_poly(level)
    poly2 = generate_poly(level)
    
    if op == '+':
        correct = add_polynomials(poly1, poly2)
    elif op == '-':
        correct = subtract_polynomials(poly1, poly2)
    elif op == '*':
        correct = multiply_polynomials(poly1, poly2)
    else:
        correct = divide_polynomials(poly1, poly2)
    
    question = f"計算 ${poly1} {op} {poly2}$"
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
    for deg in range(random.randint(1, max_degree), -1, -1):
        coeff = random.randint(-5, 5)
        if coeff == 0:
            continue
        if deg == 0:
            terms.append(f"{coeff}")
        elif deg == 1:
            terms.append(f"{coeff}x")
        else:
            terms.append(f"{coeff}x^{deg}")
    return " + ".join(terms).replace("+ -", "- ")

def add_polynomials(p1, p2):
    return combine_polynomials(p1, p2, '+')

def subtract_polynomials(p1, p2):
    return combine_polynomials(p1, p2, '-')

def multiply_polynomials(p1, p2):
    return expand_polynomials(p1, p2)

def divide_polynomials(p1, p2):
    return simplify_polynomials(p1, p2)

def combine_polynomials(p1, p2, op):
    terms1 = parse_polynomial(p1)
    terms2 = parse_polynomial(p2)
    
    for term in terms2:
        if op == '+':
            terms1[term] = terms1.get(term, 0) + terms2[term]
        else:
            terms1[term] = terms1.get(term, 0) - terms2[term]
    
    return format_polynomial(terms1)

def expand_polynomials(p1, p2):
    terms1 = parse_polynomial(p1)
    terms2 = parse_polynomial(p2)
    result = {}
    
    for t1, c1 in terms1.items():
        for t2, c2 in terms2.items():
            deg = t1[1] + t2[1]
            coeff = c1 * c2
            key = (t1[0] +