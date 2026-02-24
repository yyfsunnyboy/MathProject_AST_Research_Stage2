import random

def generate(level=1, **kwargs):
    c = random.choice([i for i in range(-12, 13) if i != 0])
    q = random.randint(-10, 10)
    s = c * q
    a = random.randint(-30, 30)
    b = s - a
    d = random.randint(-10, 10)
    e = random.randint(-12, 12)
    f = random.randint(-12, 12)
    g = random.randint(-30, 30)
    def p(n):
        return f"({n})" if n < 0 else str(n)
    p1_s = f"[{p(a)}+{p(b)}]÷{p(c)}×{p(d)}"
    p1_v = q * d
    gs = "+" if g >= 0 else ""
    p2_s = f"|{p(e)}×{p(f)}{gs}{g}|"
    p2_v = abs(e * f + g)
    op = random.choice(['+', '-'])
    if op == '+':
        ans = p1_v + p2_v
    else:
        ans = p1_v - p2_v
    return {
        'question_text': f"計算 {p1_s}{op}{p2_s} 的值。",
        'answer': '',
        'correct_answer': str(ans),
        'mode': 1
    }

def check(user_answer, correct_answer):
    res = str(user_answer).strip() == str(correct_answer).strip()
    return {
        'correct': res,
        'result': '正確' if res else '錯誤'
    }