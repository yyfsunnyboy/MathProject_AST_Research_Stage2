import random

def generate(level=1, **kwargs):
    a = random.randint(-25, 25)
    b = random.randint(-25, 25)
    op1 = random.choice(['+', '-'])
    p1_v = a + b if op1 == '+' else a - b
    c_l = [i for i in range(-12, 13) if i != 0 and p1_v % i == 0]
    c = random.choice(c_l) if c_l else 1
    d = random.randint(-10, 10)
    e = random.randint(-10, 10)
    f = random.randint(-10, 10)
    g = random.randint(-25, 25)
    op2 = random.choice(['+', '-'])
    op3 = random.choice(['+', '-'])
    def f_n(n): return f"({n})" if n < 0 else str(n)
    q = f"[{f_n(a)}{op1}{f_n(b)}]÷{f_n(c)}×{f_n(d)}{op2}|{f_n(e)}×{f_n(f)}{op3}{f_n(g)}|"
    v1 = (p1_v // c) * d
    v2_i = e * f + g if op3 == '+' else e * f - g
    v2 = abs(v2_i)
    ans = v1 + v2 if op2 == '+' else v1 - v2
    return {
        'question_text': f"計算 {q} 的值。",
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