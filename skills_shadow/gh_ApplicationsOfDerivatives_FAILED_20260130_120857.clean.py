def generate(level=1, **kwargs):
    op_latex = {'+': '+', '-': '-', '*': '\\times', '/': '\\div'}
    max_degree = random.randint(3, 5)
    polynomial_coefficients = []
    for _safety_loop_var in range(1000):
        for _ in range(max_degree + 1):
            coeff = random.randint(-10, 10)
            if len(polynomial_coefficients) == 0 and coeff == 0:
                continue
            polynomial_coefficients.append(coeff)
        has_negative = any((c < 0 for c in polynomial_coefficients))
        has_non_zero_constant = polynomial_coefficients[-1] != 0
        if has_negative and has_non_zero_constant:
            break
    derivative_orders_to_find = set()
    while len(derivative_orders_to_find) < 2:
        order = random.randint(1, max_degree - 1)
        derivative_orders_to_find.add(order)
    current_coefficients = polynomial_coefficients[:]
    derivative_results = {}
    for _ in range(max(derivative_orders_to_find)):
        next_coefficients = []
        for i, coeff in enumerate(current_coefficients):
            if i == len(current_coefficients) - 1:
                break
            new_coeff = coeff * (len(current_coefficients) - 1 - i)
            next_coefficients.append(new_coeff)
        current_degree = max_degree - len(next_coefficients)
        if current_degree in derivative_orders_to_find:
            derivative_results[current_degree] = next_coefficients[:]
        current_coefficients = next_coefficients
    poly_terms = []
    for i, coeff in enumerate(polynomial_coefficients):
        degree = max_degree - i
        if coeff == 0:
            continue
        coeff_str = fmt_num(abs(coeff))
        if degree == 0:
            term = coeff_str
        elif degree == 1:
            term = f'{coeff_str}x' if coeff_str != '1' else 'x'
        else:
            term = f'{coeff_str}x^{{{degree}}}' if coeff_str != '1' else f'x^{{{degree}}}'
        if coeff < 0:
            poly_terms.append(f"{op_latex['-']}{term}")
        elif len(poly_terms) > 0:
            poly_terms.append(f"{op_latex['+']}{term}")
        else:
            poly_terms.append(term)
    f_x_latex = ''.join(poly_terms)
    derivative_parts = []
    for order in sorted(list(derivative_orders_to_find)):
        if order == 1:
            derivative_parts.append(f"f'(x)")
        elif order == 2:
            derivative_parts.append(f"f''(x)")
        elif order == 3:
            derivative_parts.append(f"f'''(x)")
        else:
            derivative_parts.append(f'f^{{{order}}}(x)')
    question_str = f"已知 $f(x) = {f_x_latex}$, 求 {', '.join(derivative_parts)}。"
    q = clean_latex_output(question_str)
    answer_parts = []
    for order in sorted(list(derivative_orders_to_find)):
        formatted_poly = fmt_num(derivative_results[order], max_degree)
        if order == 1:
            answer_parts.append(f"f'(x) = {formatted_poly}")
        elif order == 2:
            answer_parts.append(f"f''(x) = {formatted_poly}")
        elif order == 3:
            answer_parts.append(f"f'''(x) = {formatted_poly}")
        else:
            answer_parts.append(f'f^{{{order}}}(x) = {formatted_poly}')
    final_answer = '\n'.join(answer_parts)
    return {'question_text': clean_latex_output(q), 'correct_answer': final_answer, 'answer': final_answer, 'mode': 1}