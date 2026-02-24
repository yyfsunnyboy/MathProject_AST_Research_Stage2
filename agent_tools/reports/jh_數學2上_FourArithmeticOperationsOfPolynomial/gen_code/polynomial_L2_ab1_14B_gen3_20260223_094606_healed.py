import random

def generate(level=1, **kwargs):
    ops = ['+', '-', '*']
    op = random.choice(ops)
    poly1 = generate_poly()
    poly2 = generate_poly()
    
    if op == '+':
        result = add_polynomials(poly1, poly2)
        question = f"計算 $( {format_poly(poly1)} ) + ( {format_poly(poly2)} )$"
    elif op == '-':
        result = subtract_polynomials(poly1, poly2)
        question = f"計算 $( {format_poly(poly1)} ) - ( {format_poly(poly2)} )$"
    else:
        result = multiply_polynomials(poly1, poly2)
        question = f"展開並化簡 $( {format_poly(poly1)} )( {format_poly(poly2)} )$"
    
    correct_answer = format_poly(result)
    return {
        'question_text': question,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}

def generate_poly():
    terms = []
    for _ in range(random.randint(2, 4)):
        deg = random.randint(0, 3)
        coeff = random.randint(-5, 5)
        if coeff == 0:
            continue
        terms.append((coeff, deg))
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

def format_poly(terms):
    parts = []
    for coeff, deg in terms:
        if coeff == 0:
            continue
        if deg == 0:
            parts.append(f"{coeff}")
        elif deg == 1:
            parts.append(f"{coeff}x")
        else:
            parts.append(f"{coeff}x^{deg}")
    return " + ".join(parts).replace("+ -", "- ")