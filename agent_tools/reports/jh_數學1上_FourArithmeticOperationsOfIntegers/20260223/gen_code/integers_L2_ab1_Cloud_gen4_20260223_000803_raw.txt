import random

def generate(level=1, **kwargs):
    def f(n):
        return f"({n})" if n < 0 else str(n)
    
    t = random.randint(1, 3)
    if t == 1:
        # Template: [(a + b) ÷ c] × d + |e × g + h|
        c = random.choice([i for i in range(-10, 11) if i != 0])
        k = random.randint(-10, 10)
        a = random.randint(-20, 20)
        b = c * k - a
        d = random.randint(-10, 10)
        e = random.randint(-10, 10)
        g = random.randint(-10, 10)
        h = random.randint(-20, 20)
        q = f"計算 [{f(a)}+{f(b)}]÷{f(c)}×{f(d)}+|{f(e)}×{f(g)}+{f(h)}| 的值。"
        ans = k * d + abs(e * g + h)
    elif t == 2:
        # Template: a × [b + (c - d) ÷ e] - |g × h|
        e = random.choice([i for i in range(-10, 11) if i != 0])
        k = random.randint(-10, 10)
        c = random.randint(-20, 20)
        d = c - (e * k)
        a = random.randint(-10, 10)
        b = random.randint(-10, 10)
        g = random.randint(-10, 10)
        h = random.randint(-10, 10)
        q = f"計算 {f(a)}×[{f(b)}+({f(c)}-{f(d)})÷{f(e)}]-|{f(g)}×{f(h)}| 的值。"
        ans = a * (b + k) - abs(g * h)
    else:
        # Template: |a × b - c| ÷ d + (e + g) × h
        d = random.choice([i for i in range(-10, 11) if i != 0])
        k = random.randint(-10, 10)
        target = abs(d * k)
        a = random.randint(-10, 10)
        b = random.randint(-10, 10)
        c = a * b - random.choice([target, -target])
        e = random.randint(-20, 20)
        g = random.randint(-20, 20)
        h = random.randint(-10, 10)
        q = f"計算 |{f(a)}×{f(b)}-{f(c)}|÷{f(d)}+({f(e)}+{f(g)})×{f(h)} 的值。"
        ans = int(abs(a * b - c) / d) + (e + g) * h

    return {
        'question_text': q,
        'answer': '',
        'correct_answer': str(int(ans)),
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        is_correct = str(user_answer).strip() == str(correct_answer).strip()
    except:
        is_correct = False
    return {
        'correct': is_correct,
        'result': '正確' if is_correct else '錯誤'
    }