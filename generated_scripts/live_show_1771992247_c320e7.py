def generate(level=1, **kwargs):
    question_text = ''
    a = Fraction(random.randint(-10, 10), 1)
    b = Fraction(random.randint(-10, 10), 1)
    c = Fraction(random.randint(-10, 10), 1)
    d = Fraction(random.randint(-10, 10), 1)
    e = Fraction(random.randint(-10, 10), 1)
    f = Fraction(random.randint(-10, 10), 1)
    g = Fraction(random.randint(-10, 10), 1)
    h = Fraction(random.randint(-10, 10), 1)
    i = Fraction(random.randint(-10, 10), 1)
    j = Fraction(random.randint(-10, 10), 1)
    k = Fraction(random.randint(-10, 10), 1)
    l = Fraction(random.randint(-10, 10), 1)
    m = Fraction(random.randint(-10, 10), 1)
    n = Fraction(random.randint(-10, 10), 1)
    o = Fraction(random.randint(-10, 10), 1)
    p = Fraction(random.randint(-10, 10), 1)
    q = Fraction(random.randint(-10, 10), 1)
    r = Fraction(random.randint(-10, 10), 1)
    s = Fraction(random.randint(-10, 10), 1)
    t = Fraction(random.randint(-10, 10), 1)
    u = Fraction(random.randint(-10, 10), 1)
    v = Fraction(random.randint(-10, 10), 1)
    w = Fraction(random.randint(-10, 10), 1)
    x = Fraction(random.randint(-10, 10), 1)
    y = Fraction(random.randint(-10, 10), 1)
    z = Fraction(random.randint(-10, 10), 1)
    question_text = f'\\left[({a} \\times {b}) + \\left(\\left| {c} \\times {d} - {e} \\right| \\times {f} \\right) \\right] \\div \\left(\\left| {g} \\times {h} - {i} \\right| + {j} \\right) + \\left| {k} \\times \\left(\\left| {l} \\times {m} - {n} \\right| \\div {o} \\right) - {p} \\right| \\times {q} \\div \\left(\\left| {r} \\times {s} - {t} \\right| + {u} \\right) - \\left(\\left| {v} \\times {w} - {x} \\right| \\div {y} \\right) \\times {z}'
    result = (a * b + abs(c * d - e) * f) / (abs(g * h - i) + j) + abs(k * abs(l * m - n) / o - p) * q / (abs(r * s - t) + u) - abs(v * w - x) / y * z
    correct_answer = f'{result.numerator}/{result.denominator}' if result.denominator != 1 else f'{result.numerator}'
    return {'question_text': question_text, 'answer': '', 'correct_answer': correct_answer, 'mode': 1}

def check(user_answer, correct_answer):
    return safe_eval(user_answer) == safe_eval(correct_answer)