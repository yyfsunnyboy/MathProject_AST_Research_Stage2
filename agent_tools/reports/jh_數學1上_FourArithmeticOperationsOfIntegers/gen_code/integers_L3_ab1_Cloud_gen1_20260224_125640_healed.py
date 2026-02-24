import random

def generate(level=1, **kwargs):
    c = random.choice([i for i in range(-12, 13) if i != 0])
    q_p = random.randint(-10, 10)
    num = c * q_p
    a = random.randint(-50, 50)
    b = num - a
    d = random.randint(-10, 10)
    e = random.randint(-12, 12)
    f = random.randint(-12, 12)
    g = random.randint(-50, 50)
    op = random.choice(['+', '-'])
    v1 = q_p * d
    v2 = abs(e * f - g)
    ans = v1 + v2 if op == '+' else v1 - v2
    def f_n(n):
        return f"({n})" if n < 0 else str(n)
    txt = f"計算 [{f_n(a)}+{f_n(b)}]÷{f_n(c)}×{f_n(d)}{op}|{f_n(e)}×{f_n(f)}-{f_n(g)}| 的值。"
    return {
        'question_text': txt,
        'answer': '',
        'correct_answer': str(ans),
        'mode': 1
    }

def check(user_answer, correct_answer):
    is_c = str(user_answer).strip() == str(correct_answer).strip()
    return {
        'correct': is_c,
        'result': '正確' if is_c else '錯誤'
    }