import random

def generate(level=1, **kwargs):
    def f(n):
        return f"({n})" if n < 0 else str(n)
    
    t = random.randint(1, 3)
    if t == 1:
        c = random.choice([i for i in range(-10, 11) if i != 0])
        m = random.randint(-6, 6)
        s = c * m
        a = random.randint(-20, 20)
        b = s - a
        d = random.randint(-10, 10)
        v1 = random.randint(-10, 10)
        v2 = random.randint(-10, 10)
        v3 = random.choice([i for i in range(-20, 21) if i != 0])
        expr = f"[{f(a)}+{f(b)}]÷{f(c)}×{f(d)}+|{f(v1)}×{f(v2)}{'+' if v3>0 else ''}{v3}|"
        res = m * d + abs(v1 * v2 + v3)
    elif t == 2:
        a = random.randint(-10, 10)
        b = random.randint(-15, 15)
        c = random.randint(-15, 15)
        g = random.choice([i for i in range(-8, 9) if i != 0])
        m = random.randint(-5, 5)
        v1 = random.randint(-10, 10)
        v2 = random.randint(-10, 10)
        d = g * m - (v1 * v2)
        expr = f"{f(a)}×({f(b)}-{f(c)})+[{f(d)}+({f(v1)}×{f(v2)})]÷{f(g)}"
        res = a * (b - c) + m
    else:
        v1 = random.randint(-10, 10)
        v2 = random.randint(-10, 10)
        v3 = random.choice([i for i in range(-20, 21) if i != 0])
        a = random.randint(-15, 15)
        b = random.randint(-15, 15)
        c = random.randint(-5, 5)
        expr = f"|{f(v1)}×{f(v2)}{'+' if v3>0 else ''}{v3}|-({f(a)}+{f(b)})×{f(c)}"
        res = abs(v1 * v2 + v3) - (a + b) * c

    return {
        'question_text': f"計算 {expr} 的值。",
        'answer': '',
        'correct_answer': str(res),
        'mode': 1
    }

def check(user_answer, correct_answer):
    is_correct = str(user_answer).strip() == str(correct_answer).strip()
    return {
        'correct': is_correct,
        'result': '正確' if is_correct else '錯誤'
    }