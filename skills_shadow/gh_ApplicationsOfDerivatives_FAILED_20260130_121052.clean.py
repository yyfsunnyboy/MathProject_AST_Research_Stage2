def generate(level=1, **kwargs):
    polynomial_degree = random.randint(3, 5)
    num_terms = random.randint(3, 5)
    original_coeffs = [0] * (polynomial_degree + 1)
    indices = list(range(polynomial_degree + 1))
    selected_indices = random.sample(indices, num_terms)
    for k in selected_indices:
        for _safety_loop_var in range(1000):
            coefficient = random.randint(-10, 10)
            if coefficient != 0:
                break
        original_coeffs[k] = coefficient
    if original_coeffs[polynomial_degree] == 0:
        original_coeffs[polynomial_degree] = safe_choice([-1, 1])
    if original_coeffs[0] == 0:
        original_coeffs[0] = safe_choice([-1, 1])
    has_positive = any((c > 0 for c in original_coeffs))
    has_negative = any((c < 0 for c in original_coeffs))
    if not has_positive:
        index_to_change = safe_choice([i for i, c in enumerate(original_coeffs) if c <= 0])
        original_coeffs[index_to_change] += 1
    if not has_negative:
        index_to_change = safe_choice([i for i, c in enumerate(original_coeffs) if c >= 0])
        original_coeffs[index_to_change] -= 1
    if all((c not in [1, -1] for c in original_coeffs)):
        index_to_change = safe_choice([i for i, c in enumerate(original_coeffs) if abs(c) > 1])
        original_coeffs[index_to_change] = safe_choice([1, -1])
    valid_derivative_orders = list(range(1, polynomial_degree))
    requested_derivative_orders = random.sample(valid_derivative_orders, 2)
    current_coeffs = original_coeffs.copy()
    derivative_results = {}
    for k in range(1, max(requested_derivative_orders) + 1):
        next_coeffs = []
        for i in range(1, len(current_coeffs)):
            new_coefficient = current_coeffs[i] * i
            next_coeffs.append(new_coefficient)
        current_coeffs = next_coeffs
        if k in requested_derivative_orders:
            derivative_results[k] = current_coeffs[:]
    ans_parts = []
    for order in sorted(requested_derivative_orders):
        coeffs = derivative_results[order]
        poly_text = build_polynomial_text(coeffs)
        if order == 1:
            ans_parts.append(f"f'(x) = {poly_text}")
        elif order == 2:
            ans_parts.append(f"f''(x) = {poly_text}")
        elif order == 3:
            ans_parts.append(f"f'''(x) = {poly_text}")
        else:
            ans_parts.append(f'f^{{{order}}}(x) = {poly_text}')
    answer = '\n'.join(ans_parts)
    return {'question_text': clean_latex_output(q), 'correct_answer': a, 'answer': a, 'mode': 1}