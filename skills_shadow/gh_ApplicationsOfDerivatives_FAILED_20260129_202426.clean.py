def generate(level=1, **kwargs):
    op_latex = {'+': '+', '-': '-', '*': '\\times', '/': '\\div'}
    func_factor1_coeff = safe_choice([-1, 1])
    while func_factor1_coeff * tangent_x0 + func_factor1_const == 0:
        func_factor1_coeff = safe_choice([-1, 1])
    func_factor1_const = random.randint(-5, 5)
    while func_factor1_coeff * tangent_x0 + func_factor1_const == 0:
        func_factor1_const = random.randint(-5, 5)
    func_factor2_coeff = safe_choice([-3, -2, 2, 3])
    while func_factor2_coeff * tangent_x0 + func_factor2_const in [0, 1, -1]:
        func_factor2_coeff = safe_choice([-3, -2, 2, 3])
    func_factor2_const = random.randint(-5, 5)
    while func_factor2_coeff * tangent_x0 + func_factor2_const == 0:
        func_factor2_const = random.randint(-5, 5)
    func_factor2_power = safe_choice([2, 3])
    tangent_x0 = safe_choice([-2, -1, 1, 2])
    while func_factor2_coeff * tangent_x0 + func_factor2_const in [0, 1, -1]:
        tangent_x0 = safe_choice([-2, -1, 1, 2])
    term1_str = f"{fmt_num(func_factor1_coeff)}x{op_latex['+']}{fmt_num(func_factor1_const)}"
    if func_factor1_coeff == 1:
        term1_str = 'x' + op_latex['+'] + fmt_num(func_factor1_const)
    elif func_factor1_coeff == -1:
        term1_str = '-x' + op_latex['+'] + fmt_num(func_factor1_const)
    term2_str = f"{fmt_num(func_factor2_coeff)}x{op_latex['+']}{fmt_num(func_factor2_const)}"
    if func_factor2_coeff == 1:
        term2_str = 'x' + op_latex['+'] + fmt_num(func_factor2_const)
    elif func_factor2_coeff == -1:
        term2_str = '-x' + op_latex['+'] + fmt_num(func_factor2_const)
    func_expr = f'({term1_str})({term2_str})^{{{fmt_num(func_factor2_power)}}}'
    f_x_latex = f'f(x) = {func_expr}'
    tangent_y0 = (func_factor1_coeff * tangent_x0 + func_factor1_const) * (func_factor2_coeff * tangent_x0 + func_factor2_const) ** func_factor2_power
    m = func_factor1_coeff * (func_factor2_coeff * tangent_x0 + func_factor2_const) ** func_factor2_power + (func_factor1_coeff * tangent_x0 + func_factor1_const) * func_factor2_power * (func_factor2_coeff * tangent_x0 + func_factor2_const) ** (func_factor2_power - 1) * func_factor2_coeff
    b_intercept = tangent_y0 - m * tangent_x0
    point_latex = f'P({fmt_num(tangent_x0)}, {fmt_num(tangent_y0)})'
    q = f'在函數 {f_x_latex} 的圖形上, 求以點 {point_latex} 為切點的切線方程式。'
    q = clean_latex_output(q)
    if m == 1:
        slope_str = 'x'
    elif m == -1:
        slope_str = '-x'
    else:
        slope_str = f'{m}x'
    if b_intercept > 0:
        intercept_str = f'+{b_intercept}'
    elif b_intercept < 0:
        intercept_str = str(b_intercept)
    else:
        intercept_str = ''
    answer = f'y={slope_str}{intercept_str}'
    return {'question_text': q, 'correct_answer': answer, 'answer': answer, 'mode': 1}