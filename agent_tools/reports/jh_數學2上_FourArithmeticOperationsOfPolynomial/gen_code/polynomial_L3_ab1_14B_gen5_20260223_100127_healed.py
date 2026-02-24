import random

def generate(level=1, **kwargs):
    ops = ['+', '-', '*', '/']
    op = random.choice(ops)
    poly1 = []
    poly2 = []
    max_degree = 2 + level
    max_coeff = 5 + level * 2

    for _ in range(random.randint(1, max_degree + 1)):
        deg = random.randint(0, max_degree)
        coeff = random.randint(-max_coeff, max_coeff)
        if coeff != 0:
            poly1.append((coeff, deg))
    for _ in range(random.randint(1, max_degree + 1)):
        deg = random.randint(0, max_degree)
        coeff = random.randint(-max_coeff, max_coeff)
        if coeff != 0:
            poly2.append((coeff, deg))

    if op == '+':
        result = add_polynomials(poly1, poly2)
        question = f"計算 $( {' + '.join([f'{coeff}x^{deg}' for coeff, deg in poly1])} ) + ( {' + '.join([f'{coeff}x^{deg}' for coeff, deg in poly2])} )$"
    elif op == '-':
        result = subtract_polynomials(poly1, poly2)
        question = f"計算 $( {' + '.join([f'{coeff}x^{deg}' for coeff, deg in poly1])} ) - ( {' + '.join([f'{coeff}x^{deg}' for coeff, deg in poly2])} )$"
    elif op == '*':
        result = multiply_polynomials(poly1, poly2)
        question = f"展開並化簡 $( {' + '.join([f'{coeff}x^{deg}' for coeff, deg in poly1])} ) ( {' + '.join([f'{coeff}x^{deg}' for coeff, deg in poly2])} )$"
    else:
        while True:
            poly2 = generate_random_polynomial(max_degree, max_coeff)
            if is_divisible(poly1, poly2):
                break
        result = divide_polynomials(poly1, poly2)
        question = f"計算 $( {' + '.join([f'{coeff}x^{deg}' for coeff, deg in poly1])} ) ÷ ( {' + '.join([f'{coeff}x^{deg}' for coeff, deg in poly2])} )$"

    correct_answer = format_polynomial(result)
    return {
        'question_text': question,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}

def add_polynomials(p1, p2):
    result = {}
    for coeff, deg in p1 + p2:
        result[deg] = result.get(deg, 0) + coeff
    return [(v, k) for k, v in result.items()]

def subtract_polynomials(p1, p2):
    result = {}
    for coeff, deg in p1:
        result[deg] = result.get(deg, 0) + coeff
    for coeff, deg in p2:
        result[deg] = result.get(deg, 0) - coeff
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
    result = {}
    p2_deg = max(p2, key=lambda x: x[1])[1]
    p2_coeff = max(p2, key=lambda x: x[0])[0]
    for c1, d1 in p1:
        deg = d1 - p2_deg
        coeff = c1 // p2_coeff
        result[deg] = result.get(deg, 0) + coeff
    return [(v, k) for k, v in result.items()]

def is_divisible(p1, p2):
    p2_deg = max(p2, key=lambda x: x[1])[1]
    p2_coeff = max(p2, key=lambda x: x[0])[0]
    for c1, d1 in p1:
        if (d1 - p2_deg) < 0 or (c1 % p2_coeff) != 0:
            return False
    return True

def generate_random_polynomial(max_degree, max_coeff):
    poly = []
    for _ in range(random.randint(1, max_degree + 1)):
        deg = random.randint(0, max_degree)
        coeff = random.randint(-max_coeff, max_coeff)
        if coeff != 0:
            poly.append((coeff, deg))
    return poly

def format_polynomial(poly):
    terms = []
    for coeff, deg in poly:
        if coeff > 0 and len(terms) > 0: