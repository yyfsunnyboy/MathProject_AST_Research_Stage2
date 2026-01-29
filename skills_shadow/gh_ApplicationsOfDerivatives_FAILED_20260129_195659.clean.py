def generate(level=1, **kwargs):
    op_latex = {'+': '+', '-': '-', '*': '\\times', '/': '\\div'}
    a = safe_choice([-2, -1, 1, 2])
    b = random.randint(-5, 5)
    c = safe_choice([1, 2, 3])
    d = random.randint(-5, 5)
    n = safe_choice([2, 3])
    for _safety_loop_var in range(1000):
        x0 = random.randint(-2, 2)
        if c * x0 + d != 0 and a * x0 + b != 0:
            break
    y0 = (a * x0 + b) * (c * x0 + d) ** n
    term1 = (c * x0 + d) ** (n - 1)
    term2 = (a * c + a * n * c) * x0 + (a * d + b * n * c)
    slope = term1 * term2
    while slope == 0:
        a = safe_choice([-2, -1, 1, 2])
        b = random.randint(-5, 5)
        c = safe_choice([1, 2, 3])
        d = random.randint(-5, 5)
        n = safe_choice([2, 3])
        for _safety_loop_var in range(1000):
            x0 = random.randint(-2, 2)
            if c * x0 + d != 0 and a * x0 + b != 0:
                break
        y0 = (a * x0 + b) * (c * x0 + d) ** n
        term1 = (c * x0 + d) ** (n - 1)
        term2 = (a * c + a * n * c) * x0 + (a * d + b * n * c)
        slope = term1 * term2
    y_intercept = y0 - slope * x0
    term1_x = '' if a == 1 else fmt_num(a)
    term1_b = '' if b == 0 else op_latex['+'] + fmt_num(abs(b)) if b > 0 else op_latex['-'] + fmt_num(abs(b))
    if b == 0 and a == 0:
        term1_x = fmt_num(0)
    elif b == 0:
        term1_x = f'{term1_x}x'
    else:
        term1_x = f'{term1_x}x{term1_b}'
    term2_x = '' if c == 1 else fmt_num(c)
    term2_d = '' if d == 0 else op_latex['+'] + fmt_num(abs(d)) if d > 0 else op_latex['-'] + fmt_num(abs(d))
    if d == 0 and c == 0:
        term2_x = fmt_num(0)
    elif d == 0:
        term2_x = f'{term2_x}x'
    else:
        term2_x = f'{term2_x}x{term2_d}'
    fx_str = f"({term1_x})({term2_x}){op_latex['^']}{fmt_num(n)}"
    point_str = f'P({fmt_num(x0)}, {fmt_num(y0)})'
    q = f'在函數 f(x) = {fx_str} 的圖形上, 求以點 {point_str} 為切點的切線方程式。'
    q = clean_latex_output(q)
    slope_str = ''
    if slope == 1:
        slope_str = 'x'
    elif slope == -1:
        slope_str = '-x'
    else:
        slope_str = f'{slope}x'
    intercept_str = ''
    if y_intercept > 0:
        intercept_str = f' + {y_intercept}'
    elif y_intercept < 0:
        intercept_str = f' - {abs(y_intercept)}'
    answer_str = f'y = {slope_str}{intercept_str}'
    return {'question_text': q, 'correct_answer': answer_str, 'answer': answer_str, 'mode': 1}