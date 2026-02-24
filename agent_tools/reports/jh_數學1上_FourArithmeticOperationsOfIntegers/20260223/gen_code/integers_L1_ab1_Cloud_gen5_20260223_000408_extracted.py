import random

def generate(level=1, **kwargs):
    def f(n):
        return f"({n})" if n < 0 else str(n)
    t = random.randint(1, 2)
    if t == 1:
        while True:
            a, b = random.randint(-20, 20), random.randint(-20, 20)
            c = random.choice([i for i in range(-10, 11) if i != 0])
            if (a + b) % c == 0:
                d, e, g, h = random.randint(-10, 10), random.randint(-10, 10), random.randint(-10, 10), random.randint(-20, 20)
                op = random.choice(['+', '-'])
                q = f"[{f(a)}+{f(b)}]÷{f(c)}×{f(d)}{op}|{f(e)}×{f(g)}-{f(h)}|"
                p1 = int(((a + b) / c) * d)
                p2 = abs(e * g - h)
                ans = p1 + p2 if op == '+' else p1 - p2
                break
    else:
        while True:
            a, b, c, d = random.randint(-10, 10), random.randint(-10, 10), random.randint(-10, 10), random.randint(-10, 10)
            e = random.choice([i for i in range(-10, 11) if i != 0])
            if (c * d) % e == 0:
                g = random.randint(-20, 20)
                q = f"{f(a)}×{f(b)}-[{f(c)}×{f(d)}÷{f(e)}+{f(g)}]"
                ans = (a * b) - (int((c * d) / e) + g)
                break
    return {'question_text': f"計算 {q} 的值。", 'answer': '', 'correct_answer': str(ans), 'mode': 1}

def check(user_answer, correct_answer):
    res = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': res, 'result': '正確' if res else '錯誤'}