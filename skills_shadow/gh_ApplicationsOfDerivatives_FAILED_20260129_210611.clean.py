def generate(level=1, **kwargs):

    def random_fraction(min_v, max_v, min_den=2, max_den=10, *args):
        num = random.randint(min_v, max_v)
        den = random.randint(min_den, max_den)
        return Fraction(num, den) if den != 0 else Fraction(num, 1)

    def polynomial_to_string(coeffs, variable='x'):
        terms = []
        degree = len(coeffs) - 1
        for i in range(degree + 1):
            coeff = coeffs[i]
            if coeff == 0:
                continue
            term = ''
            if abs(coeff) != 1 or i == 0:
                term += str(Fraction(coeff))
            if degree - i > 1:
                term += f'{variable}^{degree - i}'
            elif degree - i == 1:
                term += variable
            terms.append(term)
        return ' + '.join(terms)

    def polynomial_derivative(coeffs, order):
        for _ in range(order):
            new_coeffs = []
            degree = len(coeffs) - 1
            for i in range(degree):
                new_coeffs.append(Fraction(i + 1) * coeffs[i])
            if not new_coeffs:
                return [0]
            coeffs = new_coeffs
        return coeffs

    def get_random_fraction():
        numerator = randint(-10, 10)
        denominator = choice([2, 3, 4, 5])
        while numerator == 0 or (numerator % denominator == 0 and abs(numerator // denominator) > 10):
            numerator = randint(-10, 10)
        return Fraction(numerator, denominator)

    def get_random_integer():
        return randint(-10, 10)
    degree = randint(2, 5)
    coeffs = [get_random_fraction() if choice([True, False]) else get_random_integer() for _ in range(degree + 1)]
    while abs(coeffs[degree]) == 0:
        coeffs[degree] = get_random_fraction() if choice([True, False]) else get_random_integer()
    non_zero_count = sum((1 for c in coeffs if c != 0))
    while non_zero_count < 3 or all((abs(c) <= 1 for c in coeffs)):
        coeffs[randint(0, degree)] = get_random_fraction() if choice([True, False]) else get_random_integer()
        non_zero_count = sum((1 for c in coeffs if c != 0))
    order1 = randint(1, degree)
    order2 = randint(1, degree)
    while order2 == order1:
        order2 = randint(1, degree)
    final_coeffs_1 = polynomial_derivative(coeffs, order1)
    final_coeffs_2 = polynomial_derivative(coeffs, order2)
    while any((abs(c) > 100 for c in coeffs + final_coeffs_1 + final_coeffs_2)):
        coeffs = [get_random_fraction() if choice([True, False]) else get_random_integer() for _ in range(degree + 1)]
        while abs(coeffs[degree]) == 0:
            coeffs[degree] = get_random_fraction() if choice([True, False]) else get_random_integer()
        non_zero_count = sum((1 for c in coeffs if c != 0))
        while non_zero_count < 3 or all((abs(c) <= 1 for c in coeffs)):
            coeffs[randint(0, degree)] = get_random_fraction() if choice([True, False]) else get_random_integer()
            non_zero_count = sum((1 for c in coeffs if c != 0))
        final_coeffs_1 = polynomial_derivative(coeffs, order1)
        final_coeffs_2 = polynomial_derivative(coeffs, order2)
    poly_str_f = fmt_num(coeffs)
    f_prime_symbol_1 = "f'" if order1 == 1 else "f''" if order1 == 2 else "f'''" if order1 == 3 else f'f^{{({order1})}}'
    f_prime_symbol_2 = "f'" if order2 == 1 else "f''" if order2 == 2 else "f'''" if order2 == 3 else f'f^{{({order2})}}'
    q = f'已知 f(x) = {poly_str_f}, 求 {f_prime_symbol_1}(x) 與 {f_prime_symbol_2}(x)。'
    q = clean_latex_output(q)
    poly_str_ans_1 = polynomial_to_string(final_coeffs_1)
    poly_str_ans_2 = polynomial_to_string(final_coeffs_2)
    ans = f'{f_prime_symbol_1}(x) = {poly_str_ans_1}\n{f_prime_symbol_2}(x) = {poly_str_ans_2}'
    return {'question_text': q, 'correct_answer': ans, 'answer': ans, 'mode': 1}