def generate(level=1, **kwargs):
    for _safety_loop_var in range(1000):
        degree = safe_choice([3, 4, 5])
        polynomial_coeffs = [0] * (degree + 1)
        polynomial_coeffs[degree] = safe_choice([i for i in range(-10, 11) if i != 0])
        for i in range(degree):
            polynomial_coeffs[i] = random.randint(-10, 10)
        non_zero_count = sum((1 for c in polynomial_coeffs if c != 0))
        if non_zero_count < 3:
            continue
        derivative_order_1 = random.randint(1, degree)
        derivative_order_2 = random.randint(1, degree)
        while derivative_order_2 == derivative_order_1:
            derivative_order_2 = random.randint(1, degree)
        current_coeffs = list(polynomial_coeffs)
        f_prime1_coeffs = []
        f_prime2_coeffs = []
        max_order = max(derivative_order_1, derivative_order_2)
        for i in range(1, max_order + 1):
            next_coeffs = []
            for j in range(1, len(current_coeffs)):
                next_coeffs.append(current_coeffs[j] * j)
            current_coeffs = next_coeffs
            if i == derivative_order_1:
                f_prime1_coeffs = list(current_coeffs)
            if i == derivative_order_2:
                f_prime2_coeffs = list(current_coeffs)
        coeff_abs_check_passed = True
        for c in f_prime1_coeffs:
            if abs(c) > 1000:
                coeff_abs_check_passed = False
                break
        if not coeff_abs_check_passed:
            continue
        for c in f_prime2_coeffs:
            if abs(c) > 1000:
                coeff_abs_check_passed = False
                break
        if not coeff_abs_check_passed:
            continue
        break
    f_x_latex = fmt_polynomial(polynomial_coeffs, is_latex=True)
    prime1_symbol_latex = fmt_num(derivative_order_1)
    prime2_symbol_latex = fmt_num(derivative_order_2)
    q = f'已知 $f(x) = {f_x_latex}$, 求 {prime1_symbol_latex} 與 {prime2_symbol_latex}。'  # 多項式已格式化，不需 clean_latex_output
    f_prime1_plain = fmt_polynomial(f_prime1_coeffs, is_latex=False)
    f_prime2_plain = fmt_polynomial(f_prime2_coeffs, is_latex=False)

    def get_plain_derivative_symbol(order):
        if order == 1:
            return "f'(x)"
        elif order == 2:
            return "f''(x)"
        else:
            return f'f^({order})(x)'
    prime1_symbol_plain = get_plain_derivative_symbol(derivative_order_1)
    prime2_symbol_plain = get_plain_derivative_symbol(derivative_order_2)
    a = f'{prime1_symbol_plain} = {f_prime1_plain}\n{prime2_symbol_plain} = {f_prime2_plain}'
    return {'question_text': q, 'correct_answer': a, 'answer': a, 'mode': 1}