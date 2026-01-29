def generate(level=1, **kwargs):
    op_latex = {'+': '+', '-': '-', '*': '\\times', '/': '\\div'}
    a1 = randint(-3, 3)
    while a1 == 0:
        a1 = randint(-3, 3)
    b1 = randint(-5, 5)
    a2 = randint(-3, 3)
    while a2 == 0:
        a2 = randint(-3, 3)
    b2 = randint(-5, 5)
    n = randint(2, 3)
    x0 = randint(-3, 3)
    y0 = (a1 * x0 + b1) * (a2 * x0 + b2) ** n
    u_prime = a1
    v_prime = n * (a2 * x0 + b2) ** (n - 1) * a2
    f_prime_x0 = u_prime * (a2 * x0 + b2) ** n + (a1 * x0 + b1) * v_prime
    while f_prime_x0 == 0:
        a1 = randint(-3, 3)
        while a1 == 0:
            a1 = randint(-3, 3)
        b1 = randint(-5, 5)
        a2 = randint(-3, 3)
        while a2 == 0:
            a2 = randint(-3, 3)
        b2 = randint(-5, 5)
        n = randint(2, 3)
        x0 = randint(-3, 3)
    y0 = (a1 * x0 + b1) * (a2 * x0 + b2) ** n
    u_prime = a1
    v_prime = n * (a2 * x0 + b2) ** (n - 1) * a2
    f_prime_x0 = u_prime * (a2 * x0 + b2) ** n + (a1 * x0 + b1) * v_prime
    m = Fraction(f_prime_x0)
    b = y0 - m * x0

    def fmt_num_coeff(coeff):
        if coeff == 1:
            return ''
        elif coeff == -1:
            return '-'
        else:
            return str(coeff)
    sign_b1 = '+' if b1 >= 0 else '-'
    abs_b1 = abs(b1)
    sign_b2 = '+' if b2 >= 0 else '-'
    abs_b2 = abs(b2)
    f_x_str = f'({fmt_num_coeff(a1)}x {op_latex[sign_b1]} {abs_b1})({fmt_num_coeff(a2)}x {op_latex[sign_b2]} {abs_b2})^{n}'
    x0_str = fmt_num(x0)
    y0_str = fmt_num(y0)
    q = f'在函數 f(x) = {f_x_str} 的圖形上, 求以點 P({x0_str}, {y0_str}) 為切點的切線方程式。'
    q = clean_latex_output(q)
    m_str = str(m) if m != 1 and m != -1 else '' if m == 1 else '-'
    b_str = str(b) if b >= 0 else f'-{abs(b)}'
    if m == 1:
        a = f'y = x + {b_str}'
    elif m == -1:
        a = f'y = -x + {b_str}'
    else:
        a = f'y = {m_str}x + {b_str}'
    return {'question_text': q, 'correct_answer': a, 'answer': a, 'mode': 1}