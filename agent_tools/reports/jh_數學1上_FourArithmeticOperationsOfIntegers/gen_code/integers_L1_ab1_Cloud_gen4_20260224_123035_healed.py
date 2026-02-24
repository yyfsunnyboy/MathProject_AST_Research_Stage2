import random

def generate(level=1, **kwargs):
    c = random.choice([i for i in range(-12, 13) if i != 0])
    k = random.randint(-10, 10)
    a = random.randint(-30, 30)
    b = k * c - a
    d = random.randint(-10, 10)
    e = random.randint(-10, 10)
    f = random.randint(-10, 10)
    g = random.randint(-30, 30)
    def f_n(n):
        return f"({n})" if n < 0 else str(n)
    p1 = k * d
    p2 = abs(e * f - g)
    op = random.choice(['+', '-'])
    ans = p1 + p2 if op == '+' else p1 - p2
    txt = f"計算 [{f_n(a)}+{f_n(b)}]÷{f_n(c)}×{f_n(d)}{op}|{f_n(e)}×{f_n(f)}-{f_n(g)}| 的值。"
    return {
        'question_text': txt,
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