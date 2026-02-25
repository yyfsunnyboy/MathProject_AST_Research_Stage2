def generate(level=1, **kwargs):
    question_text = ''
    a = Fraction(random.randint(1, 10), 1)
    b = Fraction(random.randint(1, 10), 1)
    c = Fraction(random.randint(1, 10), 1)
    d = Fraction(random.randint(1, 10), 1)
    e = Fraction(random.randint(1, 10), 1)
    f = Fraction(random.randint(1, 10), 1)
    g = Fraction(random.randint(1, 10), 1)
    h = Fraction(random.randint(1, 10), 1)
    i = Fraction(random.randint(1, 10), 1)
    j = Fraction(random.randint(1, 10), 1)
    k = Fraction(random.randint(1, 10), 1)
    l = Fraction(random.randint(1, 10), 1)
    m = Fraction(random.randint(1, 10), 1)
    n = Fraction(random.randint(1, 10), 1)
    o = Fraction(random.randint(1, 10), 1)
    p = Fraction(random.randint(1, 10), 1)
    q = Fraction(random.randint(1, 10), 1)
    r = Fraction(random.randint(1, 10), 1)
    s = Fraction(random.randint(1, 10), 1)
    t = Fraction(random.randint(1, 10), 1)
    u = Fraction(random.randint(1, 10), 1)
    v = Fraction(random.randint(1, 10), 1)
    w = Fraction(random.randint(1, 10), 1)
    x = Fraction(random.randint(1, 10), 1)
    y = Fraction(random.randint(1, 10), 1)
    z = Fraction(random.randint(1, 10), 1)
    result = (a + b) * c / d + abs(e * f - g) / h * i - j * k / l + m * n / o - p * q / r + s * t / u - v * w / x + y * z / random.randint(1, 10)
    correct_answer = f'{result.numerator}/{result.denominator}' if result.denominator != 1 else f'{result.numerator}'
    question_text = f'Calculate $$ \\left[({a.numerator}/{a.denominator} + {b.numerator}/{b.denominator}) \\times {c.numerator}/{c.denominator}\\right] \\div {d.numerator}/{d.denominator} + \\left|{e.numerator}/{e.denominator} \\times \\left(-{f.numerator}/{f.denominator}\\right) - {g.numerator}/{g.denominator}\\right| \\div {h.numerator}/{h.denominator} \\times {i.numerator}/{i.denominator} - {j.numerator}/{j.denominator} \\times {k.numerator}/{k.denominator} \\div {l.numerator}/{l.denominator} + {m.numerator}/{m.denominator} \\times {n.numerator}/{n.denominator} \\div {o.numerator}/{o.denominator} - {p.numerator}/{p.denominator} \\times {q.numerator}/{q.denominator} \\div {r.numerator}/{r.denominator} + {s.numerator}/{s.denominator} \\times {t.numerator}/{t.denominator} \\div {u.numerator}/{u.denominator} - {v.numerator}/{v.denominator} \\times {w.numerator}/{w.denominator} \\div {x.numerator}/{x.denominator} + {y.numerator}/{y.denominator} \\times {z.numerator}/{z.denominator} \\div {random.randint(1, 10)}\\right] $$'
    return {'question_text': question_text, 'answer': '', 'correct_answer': correct_answer, 'mode': 1}

def check(user_answer, correct_answer):
    user_fraction = Fraction(user_answer.replace(' ', ''))
    correct_fraction = Fraction(correct_answer.replace(' ', ''))
    return user_fraction == correct_fraction