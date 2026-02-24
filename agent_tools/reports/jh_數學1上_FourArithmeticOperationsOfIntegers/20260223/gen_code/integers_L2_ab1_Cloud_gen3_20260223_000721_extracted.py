import random

def generate(level=1, **kwargs):
    def fmt(n):
        return f"({n})" if n < 0 else str(n)

    t = random.randint(1, 3)
    if t == 1:
        # Template: [(a) + (b)] ÷ (c) × (d) + |(e) × (f) + (g)|
        c = random.choice([i for i in range(-10, 11) if i != 0])
        k = random.randint(-10, 10)
        sum_ab = c * k
        a = random.randint(-30, 30)
        b = sum_ab - a
        d = random.randint(-10, 10)
        e = random.randint(-10, 10)
        f = random.randint(-10, 10)
        g = random.randint(-30, 30)
        ans = (k * d) + abs(e * f + g)
        expr = f"[{fmt(a)}+{fmt(b)}]÷{fmt(c)}×{fmt(d)}+|{fmt(e)}×{fmt(f)}+{fmt(g)}|"
    elif t == 2:
        # Template: (a) × [(b) - (c)] + (d) ÷ (e) - |(f) × (g)|
        e = random.choice([i for i in range(-10, 11) if i != 0])
        d_div_e = random.randint(-10, 10)
        d = e * d_div_e
        a = random.randint(-10, 10)
        b = random.randint(-20, 20)
        c = random.randint(-20, 20)
        f = random.randint(-10, 10)
        g = random.randint(-10, 10)
        ans = a * (b - c) + d_div_e - abs(f * g)
        expr = f"{fmt(a)}×[{fmt(b)}-{fmt(c)}]+{fmt(d)}÷{fmt(e)}-|{fmt(f)}×{fmt(g)}|"
    else:
        # Template: |(a) × (b) + (c)| - (d) × [(e) + (f) ÷ (g)]
        g = random.choice([i for i in range(-10, 11) if i != 0])
        f_div_g = random.randint(-10, 10)
        f = g * f_div_g
        a = random.randint(-10, 10)
        b = random.randint(-10, 10)
        c = random.randint(-30, 30)
        d = random.randint(-10, 10)
        e = random.randint(-20, 20)
        ans = abs(a * b + c) - d * (e + f_div_g)
        expr = f"|{fmt(a)}×{fmt(b)}+{fmt(c)}|-{fmt(d)}×[{fmt(e)}+{fmt(f)}÷{fmt(g)}]"

    return {
        'question_text': f"計算 {expr} 的值。",
        'answer': '',
        'correct_answer': str(ans),
        'mode': 1
    }

def check(user_answer, correct_answer):
    ua = str(user_answer).strip()
    ca = str(correct_answer).strip()
    is_correct = (ua == ca)
    return {
        'correct': is_correct,
        'result': '正確' if is_correct else '錯誤'
    }