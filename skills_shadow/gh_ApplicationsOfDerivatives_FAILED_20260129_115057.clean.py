def fmt_num(x):
    return str(x) if x >= 0 else f'({x})'

def generate(level=1, **kwargs):
    for _safety_loop_var in range(1000):
        a = randint(-10, 10)
        if a != 0:
            break
    for _safety_loop_var in range(1000):
        b = randint(-10, 10)
        if b != 0:
            break
    for _safety_loop_var in range(1000):
        c = randint(-10, 10)
        if c != 0:
            break
    for _safety_loop_var in range(1000):
        d = randint(-10, 10)
        if d != 0:
            break
    for _safety_loop_var in range(1000):
        e = randint(-10, 10)
        if e != 0:
            break
    for _safety_loop_var in range(1000):
        f = randint(-10, 10)
        if f != 0:
            break
    for _safety_loop_var in range(1000):
        g = randint(-10, 10)
        if g != 0:
            break

    def f(x):
        return Fraction(a * x + b) * Fraction(c * x + d) ** e

    def f_prime(x):
        term1 = a * Fraction(c * x + d) ** e
        term2 = (a * x + b) * e * c * Fraction(c * x + d) ** (e - 1)
        return term1 + term2
    point_y = f(g)
    slope_k = f_prime(g)
    tangent_line_eq = f'y - {fmt_num(point_y)} = {fmt_num(slope_k)}(x - {fmt_num(g)})'
    assert isinstance(point_y, Fraction)
    assert isinstance(slope_k, Fraction)
    math_expr = f'y - {fmt_num(point_y)} = {fmt_num(slope_k)}(x - {fmt_num(g)})'
    q_str = f'${math_expr}$'
    question_output = clean_latex_output(q_str)
    return {'question_text': question_output, 'answer': str(slope_k), 'mode': 1}