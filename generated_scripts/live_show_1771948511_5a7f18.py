import random

def generate(level=1, **kwargs):
    def f(n):
        return f"({n})" if n < 0 else str(n)
    t = random.randint(1, 4)
    if t == 1:
        b = random.choice([i for i in range(-15, 16) if i != 0])
        r1 = random.randint(-15, 15)
        a = b * r1
        d = random.choice([i for i in range(-15, 16) if i != 0])
        r2 = random.randint(-15, 15)
        c = d * r2
        op = random.choice(['+', '-'])
        q = f"{f(a)}÷{f(b)}{op}{f(c)}÷{f(d)}="
        ans = r1 + r2 if op == '+' else r1 - r2
    elif t == 2:
        a, b, c, d = [random.randint(-12, 12) for _ in range(4)]
        op = random.choice(['+', '-'])
        q = f"{f(a)}×{f(b)}{op}{f(c)}×{f(d)}="
        ans = (a * b) + (c * d) if op == '+' else (a * b) - (c * d)
    elif t == 3:
        b = random.choice([i for i in range(-12, 13) if i != 0])
        r1 = random.randint(-12, 12)
        a = b * r1
        c, d = random.randint(-12, 12), random.randint(-12, 12)
        op = random.choice(['+', '-'])
        q = f"{f(a)}÷{f(b)}{op}{f(c)}×{f(d)}="
        ans = r1 + (c * d) if op == '+' else r1 - (c * d)
    else:
        a, b, c = [random.randint(-10, 10) for _ in range(3)]
        op = random.choice(['+', '-'])
        q = f"{f(a)}×({f(b)}{op}{f(c)})="
        ans = a * (b + c) if op == '+' else a * (b - c)
    return {
        'question_text': q,
        'answer': '',
        'correct_answer': str(ans),
        'mode': 1
    }

def check(user_answer, correct_answer):
    c = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': c, 'result': '正確' if c else '錯誤'}