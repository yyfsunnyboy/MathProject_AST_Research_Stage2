import random

def generate(level=1, **kwargs):
    ops = ['+', '*']
    op = random.choice(ops)
    poly1 = generate_poly()
    poly2 = generate_poly()
    
    if op == '+':
        question = f"計算 ${poly1} + {poly2}$"
        correct = add_polynomials(poly1, poly2)
    else:
        question = f"展開並化簡 ${poly1} \\cdot {poly2}$"
        correct = multiply_polynomials(poly1, poly2)
    
    return {
        'question_text': question,
        'answer': '',
        'correct_answer': correct,
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}

def generate_poly():
    terms = []
    degrees = [0, 1, 2]
    degree = random.choice(degrees)
    
    for d in range(degree, -1, -1):
        coeff = random.randint(-5, 5)
        if coeff == 0:
            continue
        if d == 0:
            terms.append(f"{coeff}")
        elif d == 1:
            terms.append(f"{coeff}x")
        else:
            terms.append(f"{coeff}x^{d}")
    
    return " + ".join(terms).replace("+ -", "- ")

def add_polynomials(p1, p2):
    terms1 = parse_terms(p1)
    terms2 = parse_terms(p2)
    result = {}
    
    for term, coeff in terms1.items():
        result[term] = result.get(term, 0) + coeff
    for term, coeff in terms2.items():
        result[term] = result.get(term, 0) + coeff
    
    return format_polynomial(result)

def multiply_polynomials(p1, p2):
    terms1 = parse_terms(p1)
    terms2 = parse_terms(p2)
    result = {}
    
    for t1, c1 in terms1.items():
        for t2, c2 in terms2.items():
            deg = int(t1) + int(t2)
            coeff = c1 * c2
            result[deg] = result.get(deg, 0) + coeff
    
    return format_polynomial(result)

def parse_terms(poly):
    terms = {}
    parts = poly.split()
    
    for part in parts:
        if '+' in part:
            subparts = part.split('+')
            for sp in subparts:
                parse_term(sp, terms)
        else:
            parse_term(part, terms)
    
    return terms

def parse_term(term, terms):
    if term == '':
        return
    if term[0] == '-':
        sign = -1
        term = term[1:]
    else:
        sign = 1
    
    if 'x' in term:
        if '^' in term:
            deg = int(term.split('^')[1])
        else:
            deg = 1
        coeff = sign * int(term.split('x')[0] or '1')
    else:
        deg = 0
        coeff = sign * int(term)
    
    terms[deg] = terms.get(deg, 0) + coeff

def format_polynomial(terms):
    parts = []
    sorted_terms = sorted(terms.items(), key=lambda x: x[0], reverse=True)
    
    for deg, coeff in sorted_terms:
        if coeff == 0:
            continue
        if deg == 0:
            parts.append(f"{coeff}")
        elif deg == 1:
            parts.append(f"{coeff}x")
        else:
            parts.append(f"{coeff}x^{deg}")
    
    return " + ".join(parts).replace("+ -", "- ")