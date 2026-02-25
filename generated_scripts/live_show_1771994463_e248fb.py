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
    result = a * b - c / d + abs(e * f - g) + abs(h * i - j) + abs(k * l - m) + abs(n * o - p) + abs(q * r - s) + abs(t * u - v) + abs(w * x - y) + abs(z * a - b)
    correct_answer = f'{result.numerator}/{result.denominator}' if result.denominator != 1 else f'{result.numerator}'
    question_text = f'Calculate $$ \\left[{a} \\times {b} - {c} \\div \\left(-{d}\\right)\\right] + \\left|{e} \\times \\left(-{f}\\right) - {g}\\right| + \\left|{h} \\times {i} - {j}\\right| + \\left|{k} \\times {l} - {m}\\right| + \\left|{n} \\times {o} - {p}\\right| + \\left|{q} \\times {r} - {s}\\right| + \\left|{t} \\times {u} - {v}\\right| + \\left|{w} \\times {x} - {y}\\right| + \\left|{z} \\times {a} - {b}\\right| $$'
    return {'question_text': question_text, 'answer': '', 'correct_answer': correct_answer, 'mode': 1}

def check(user_answer, correct_answer):
    user_answer = user_answer.replace(' ', '')
    correct_answer = correct_answer.replace(' ', '')
    if user_answer == correct_answer:
        return True
    try:
        user_result = Fraction(user_answer)
        correct_result = Fraction(correct_answer)
        return user_result == correct_result
    except:
        return False