import random

def generate(level=1, **kwargs):
    def f(n):
        return f"({n})" if n < 0 else str(n)
    a = random.randint(-30, 30)
    b = random.randint(-30, 30)
    s_ab = a + b
    ds = [i for i in range(-20, 21) if i != 0 and s_ab % i == 0]
    c = random.choice(ds)
    d = random.randint(-10, 10)
    p1_v = (a + b) // c * d
    p1_s = f"[{f(a)}+{f(b)}]÷{f(c)}×{f(d)}"
    e = random.randint(2, 12)
    fv = random.randint(-10, -2)
    g = random.randint(2, 20)
    p2_o = random.choice(['+', '-'])
    p2_v = abs(e * fv + g) if p2_o == '+' else abs(e * fv - g)
    p2_s = f"|{e}×{f(fv)}{p2_o}{g}|"
    c_o = random.choice(['+', '-'])
    ans = p1_v + p2_v if c_o == '+' else p1_v - p2_v
    return {
        'question_text': f"計算 {p1_s}{c_o}{p2_s} 的值。",
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