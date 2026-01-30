```
def generate(level=1, **kwargs):
    import random
    
    # Step 1: Generate necessary variables according to MASTER_SPEC
    degree = random.randint(3, 5)
    
    polynomial_coeffs = []
    while len([c for c in polynomial_coeffs if c != 0]) < 3:
        polynomial_coeffs = [random.randint(-10, 10) for _ in range(degree + 1)]
        polynomial_coeffs[degree] = random.choice([-10, -9, -8, -7, -6, -5, -4, -3, -2, -1, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    
    derivative_order_1 = random.randint(1, degree)
    while True:
        derivative_order_2 = random.randint(1, degree)
        if derivative_order_2 != derivative_order_1:
            break
    
    # Step 2: Execute calculations according to MASTER_SPEC
    def fmt_polynomial(coeffs):
        terms = []
        for i in range(len(coeffs)):
            coeff = coeffs[i]
            if coeff == 0:
                continue
            term = ""
            if abs(coeff) != 1 or i == 0:
                term += str(abs(coeff))
            if i > 0:
                term += "x"
                if i > 1:
                    term += f"^{{{i}}}"
            terms.append(term)
        return " + ".join(terms) if terms else "0"
    
    def differentiate(coeffs):
        new_coeffs = []
        for i in range(len(coeffs) - 1):
            new_coeffs.append(coeffs[i] * (len(coeffs) - 1 - i))
        return new_coeffs
    
    f_prime1_coeffs = polynomial_coeffs
    for _ in range(derivative_order_1):
        f_prime1_coeffs = differentiate(f_prime1_coeffs)
    
    f_prime2_coeffs = polynomial_coeffs
    for _ in range(derivative_order_2):
        f_prime2_coeffs = differentiate(f_prime2_coeffs)
    
    # Step 3: Build question LaTeX using fmt_num and op_latex
    f_x_latex = fmt_polynomial(polynomial_coeffs)
    
    def derivative_symbol(order):
        if order == 1:
            return "f'(x)"
        elif order == 2:
            return "f''(x)"
        else:
            return f"f^{({order})}(x)"
    
    prime1_symbol = derivative_symbol(derivative_order_1)
    prime2_symbol = derivative_symbol(derivative_order_2)
    
    q = f"已知 $f(x) = {f_x_latex}$，求 ${prime1_symbol}$ 與 ${prime2_symbol}$。"
    q = clean_latex_output(q)
    
    # Step 4: Format answer as plain text
    def fmt_polynomial_plain(coeffs):
        terms = []
        for i in range(len(coeffs)):
            coeff = coeffs[i]
            if coeff == 0:
                continue
            term = ""
            if abs(coeff) != 1 or i == 0:
                term += str(abs(coeff))
            if i > 0:
                term += "x"
                if i > 1:
                    term += f"^{i}"
            terms.append(term)
        return " + ".join(terms) if terms else "0"
    
    f_prime1_latex = fmt_polynomial_plain(f_prime1_coeffs)
    f_prime2_latex = fmt_polynomial_plain(f_prime2_coeffs)
    
    ans = f"{prime1_symbol} = {f_prime1_latex}\n{prime2_symbol} = {f_prime2_latex}"
    
    # Step 5: Return standard format
    return {
        'question_text': q,
        'correct_answer': ans,
        'answer': ans,
        'mode': 1
    }