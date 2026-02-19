import random

def generate(level=1, **kwargs):
    a = random.randint(-30, 30)
    b = random.randint(-30, 30)
    while a + b == 0:
        b = random.randint(-30, 30)
    sum_ab = a + b
    divisors = [i for i in range(-20, 21) if i != 0 and sum_ab % i == 0]
    c = random.choice(divisors)
    d = random.randint(-10, 10)
    e = random.randint(-12, 12)
    f = random.randint(-12, 12)
    g_val = random.randint(-30, 30)
    def f_n(n):
        return f"({n})" if n < 0 else str(n)
    if g_val >= 0:
        abs_expr = f"{f_n(e)}×{f_n(f)}+{g_val}"
        abs_res = e * f + g_val
    else:
        abs_expr = f"{f_n(e)}×{f_n(f)}-{abs(g_val)}"
        abs_res = e * f - abs(g_val)
    main_op = random.choice(['+', '-'])
    q_text = f"計算 [{f_n(a)}+{f_n(b)}]÷{f_n(c)}×{f_n(d)}{main_op}|{abs_expr}| 的值。"
    p1 = (a + b) // c * d
    p2 = abs(abs_res)
    ans = p1 + p2 if main_op == '+' else p1 - p2
    return {
        'question_text': q_text,
        'answer': '',
        'correct_answer': str(ans),
        'mode': 1
    }

def check(user_answer, correct_answer):
    is_correct = str(user_answer).strip() == str(correct_answer).strip()
    return {
        'correct': is_correct,
        'result': '正確' if is_correct else '錯誤'
    }