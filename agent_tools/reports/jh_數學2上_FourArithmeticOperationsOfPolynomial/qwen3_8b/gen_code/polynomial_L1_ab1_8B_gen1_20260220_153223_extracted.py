import random

def generate(level=1, **kwargs):
    def generate_polynomial(max_degree):
        terms = {}
        for degree in range(max_degree + 1):
            coeff = random.randint(-5, 5)
            terms[degree] = coeff
        if all(v == 0 for v in terms.values()):
            terms[max_degree] = 1
        return terms

    def format_poly(poly):
        terms = []
        for deg in sorted(poly.keys(), reverse=True):
            coeff = poly[deg]
            if coeff == 0:
                continue
            if deg == 0:
                term = f"{abs(coeff)}"
            elif deg == 1:
                term = f"{abs(coeff)}x"
            else:
                term = f"{abs(coeff)}x^{deg}"
            terms.append((coeff, term))
        if not terms:
            return "0"
        formatted_terms = []
        for i, (coeff, term) in enumerate(terms):
            if i == 0:
                if coeff < 0:
                    formatted_terms.append(f"-{term}")
                else:
                    formatted_terms.append(term)
            else:
                if coeff < 0:
                    formatted_terms.append(f" - {term}")
                else:
                    formatted_terms.append(f" + {term}")
        return ''.join(formatted_terms)

    mode = random.choice(['add_subtract', 'multiply'])
    if mode == 'add_subtract':
        max_degree = level
        poly1 = generate_polynomial(max_degree)
        poly2 = generate_polynomial(max_degree)
        operation = random.choice(['+', '-'])
        combined = {}
        for deg in poly1:
            combined[deg] = poly1[deg]
        for deg in poly2:
            if operation == '+':
                combined[deg] = combined.get(deg, 0) + poly2[deg]
            else:
                combined[deg] = combined.get(deg, 0) - poly2[deg]
        simplified = {deg: coeff for deg, coeff in combined.items() if coeff != 0}
        poly1_str = format_poly(poly1)
        poly2_str = format_poly(poly2)
        question = f"Calculate {poly1_str} {operation} {poly2_str}"
        correct_answer = format_poly(simplified)
        return {
            'question_text': f'Calculate {poly1_str} {operation} {poly2_str}',
            'answer': '',
            'correct_answer': correct_answer,
            'mode': 1
        }
    else:
        max_degree1 = level
        max_degree2 = level
        poly1 = generate_polynomial(max_degree1)
        poly2 = generate_polynomial(max_degree2)
        product = {}
        for deg1 in poly1:
            for deg2 in poly2:
                new_deg = deg1 + deg2
                coeff = poly1[deg1] * poly2[deg2]
                product[new_deg] = product.get(new_deg, 0) + coeff
        simplified = {deg: coeff for deg, coeff in product.items() if coeff != 0}
        poly1_str = format_poly(poly1)
        poly2_str = format_poly(poly2)
        question = f"Expand and simplify {poly1_str}({poly2_str})"
        correct_answer = format_poly(simplified)
        return {
            'question_text': f'Expand and simplify {poly1_str}({poly2_str})',
            'answer': '',
            'correct_answer': correct_answer,
            'mode': 1
        }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': 'Correct' if correct else 'Wrong'}