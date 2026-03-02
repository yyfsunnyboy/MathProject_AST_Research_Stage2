import random

def generate(level=1, **kwargs):
    def p(n):
        return f"({n})" if n < 0 else str(n)
    op_map = {
        '+': lambda a, b: a + b,
        '-': lambda a, b: a - b,
        '×': lambda a, b: a * b,
        '÷': lambda a, b: a // b
    }
    scale = level * 5
    t = random.randint(1, 3)
    if t == 1:
        a, b, c = random.randint(-scale, scale), random.randint(-scale, scale), random.randint(-scale, scale)
        o1, o2 = random.choice(['+', '-']), random.choice(['×', '÷'])
        if o2 == '÷':
            if c == 0: c = random.choice([-2, -1, 1, 2])
            b = c * random.randint(-5, 5)
        res = op_map[o1](a, op_map[o2](b, c))
        q = f"{p(a)} {o1} {p(b)} {o2} {p(c)}"
    elif t == 2:
        a, b, c = random.randint(-scale, scale), random.randint(-scale, scale), random.randint(-scale, scale)
        o1, o2 = random.choice(['×', '÷']), random.choice(['+', '-'])
        if o1 == '÷':
            inner = op_map[o2](b, c)
            if inner == 0: inner = random.choice([-2, -1, 1, 2])
            a = inner * random.randint(-5, 5)
        else:
            inner = op_map[o2](b, c)
        res = op_map[o1](a, inner)
        q = f"{p(a)} {o1} ({p(b)} {o2} {p(c)})"
    else:
        a, b, c, d = random.randint(-scale, scale), random.randint(-scale*2, scale*2), random.randint(-scale, scale), random.randint(-scale, scale)
        o1, o2, o3 = random.choice(['×', '+', '-']), random.choice(['+', '-']), '×'
        inner = op_map[o2](b, op_map[o3](c, d))
        res = op_map[o1](a, inner)
        q = f"{p(a)} {o1} [{p(b)} {o2} {p(c)} {o3} {p(d)}]"
    return {
        'question_text': q,
        'answer': '',
        'correct_answer': str(int(res)),
        'mode': 1
    }

def check(user_answer, correct_answer):
    c = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': c, 'result': '正確' if c else '錯誤'}