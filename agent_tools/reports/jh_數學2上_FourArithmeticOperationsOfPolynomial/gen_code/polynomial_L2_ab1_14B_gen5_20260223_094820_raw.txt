import random

def generate(level=1, **kwargs):
    ops = ['+', '-', '*']
    op = random.choice(ops)
    poly1 = generate_poly(level)
    poly2 = generate_poly(level)
    
    if op == '+':
        question = f"計算 ${poly1} {op} {poly2}$"
        answer = add_polynomials(poly1, poly2)
    elif op == '-':
        question = f"計算 ${poly1} {op} {poly2}$"
        answer = subtract_polynomials(poly1, poly2)
    else:
        question = f"展開並化簡 ${(poly1)} {op} {(poly2)}$"
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

def generate_poly(level):
    terms = []
    max_degree = 3 if level > 1 else 2
    num_terms = random.randint(2, 3 if level > 1 else 2)
    
    for _ in range(num_terms):
        coeff = random.randint(-5, 5)
        if coeff == 0:
            continue
        degree = random.randint(1, max_degree)
        terms.append((coeff, degree))
    
    return format_poly(terms)

def format_poly(terms):
    parts = []
    for coeff, degree in terms:
        if coeff > 0 and len(parts) > 0:
            parts.append(f"+{coeff}")
        elif coeff < 0:
            parts.append(f"{coeff}")
        else:
            continue
        
        if degree > 1:
            parts[-1] += f"x^{degree}"
        elif degree == 1:
            parts[-1] += "x"
    
    return " ".join(parts)

def add_polynomials(p1, p2):
    terms1 = parse_poly(p1)
    terms2 = parse_poly(p2)
    result = {}
    
    for coeff, degree in terms1 + terms2:
        result[degree] = result.get(degree, 0) + coeff
    
    return format_poly(sorted(result.items(), key=lambda x: x[0], reverse=True))

def subtract_polynomials(p1, p2):
    terms1 = parse_poly(p1)
    terms2 = parse_poly(p2)
    result = {}
    
    for coeff, degree in terms1:
        result[degree] = result.get(degree, 0) + coeff
    
    for coeff, degree in terms2:
        result[degree] = result.get(degree, 0) - coeff
    
    return format_poly(sorted(result.items(), key=lambda x: x[0], reverse=True))

def multiply_polynomials(p1, p2):
    terms1 = parse_poly(p1)
    terms2 = parse_poly(p2)
    result = {}
    
    for c1, d1 in terms1:
        for c2, d2 in terms2:
            degree = d1 + d2
            coeff = c1 * c2
            result[degree] = result.get(degree, 0) + coeff
    
    return format_poly(sorted(result.items(), key=lambda x: x[0], reverse=True))

def parse_poly(poly):
    terms = []
    parts = poly.replace("+", " +").replace("-", " -").split()
    
    for i in range(1, len(parts), 2):
        coeff_str = parts[i]
        if coeff_str == '1' and i+1 < len(parts) and parts[i+1].startswith('x'):
            coeff = 1
        elif coeff_str == '-1' and i+1 < len(parts) and parts[i+1].startswith('x'):
            coeff = -1
        else:
            coeff = int(coeff_str)
        
        if 'x' in parts[i+1]:
            if '^' in parts[i+1]:
                degree = int(parts[i+1].split('^')[1])
            else:
                degree = 1
        else:
            degree = 0
        
        terms.append((coeff, degree))
    
    return terms