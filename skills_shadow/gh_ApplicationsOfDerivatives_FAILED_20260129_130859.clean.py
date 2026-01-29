def fmt_num(x):
    if x < 0:
        return f'({x})'
    return str(x)
op_latex = {'+': '+', '-': '-', '*': '\\times', '/': '\\div'}

def generate(level=1, **kwargs):
    for _safety_loop_var in range(1000):
        a1 = random.randint(-3, 3)
        b1 = random.randint(-5, 5)
        a2 = random.randint(-3, 3)
        b2 = random.randint(-5, 5)
        n = safe_choice([2, 3])
        x0 = random.randint(-3, 3)
        if a1 == 0 or a2 == 0:
            continue
        term1_val_at_x0 = a1 * x0 + b1
        term2_val_at_x0 = a2 * x0 + b2
        if term2_val_at_x0 == 0:
            continue
        y0 = term1_val_at_x0 * term2_val_at_x0 ** n
        if not -50 <= y0 <= 50:
            continue
        m = a1 * term2_val_at_x0 ** n + term1_val_at_x0 * n * term2_val_at_x0 ** (n - 1) * a2
        if not -25 <= m <= 25 or m == 0:
            continue
        b_intercept = y0 - m * x0
        if not -50 <= b_intercept <= 50:
            continue
        func_str = f'({fmt_num(a1, b1)})({fmt_num(a2, b2)})^{fmt_num(n)}'
        point_str = f'P({fmt_num(x0)}, {fmt_num(y0)})'
        question_text = clean_latex_output(f'在函數 ${func_str}$ 的圖形上, 求以點 ${point_str}$ 為切點的切線方程式。')
        if m == 1:
            slope_part = 'x'
        elif m == -1:
            slope_part = '-x'
        else:
            slope_part = f'{m}x'
        if b_intercept > 0:
            intercept_part = f' + {b_intercept}'
        elif b_intercept < 0:
            intercept_part = f' - {-b_intercept}'
        else:
            intercept_part = ''
        answer_str = f'y = {slope_part}{intercept_part}'
        return {'question_text': question_text, 'answer': answer_str, 'mode': 1}