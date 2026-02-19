import random

def generate(level=1, **kwargs):
    def f(n):
        return f"({n})" if n < 0 else str(n)
    t = random.randint(1, 3)
    if t == 1:
        c = random.choice([i for i in range(-8, 9) if i != 0])
        k = random.randint(-5, 5)
        a = random.randint(-20, 20)
        b = (c * k) - a
        d = random.randint(-5, 5)
        e_val = random.randint(-10, 10)
        f_val = random.randint(-5, 5)
        g = random.randint(-15, 15)
        q = f"[{f(a)}+{f(b)}]÷{f(c)}×{f(d)}+|{f(e_val)}×{f(f_val)}+{f(g)}|"
        ans = (a + b) // c * d + abs(e_val * f_val + g)
    elif t == 2:
        e = random.choice([i for i in range(-8, 9) if i != 0])
        k = random.randint(-5, 5)
        b = random.randint(-6, 6)
        c_val = random.randint(-6, 6)
        d = (e * k) - (b * c_val)
        a = random.randint(-20, 20)
        f_val = random.randint(-20, 20)
        g = random.randint(-20, 20)
        q = f"{f(a)}-({f(b)}×{f(c_val)}+{f(d)})÷{f(e)}-|{f(f_val)}-{f(g)}|"
        ans = a - (b * c_val + d) // e - abs(f_val - g)
    else:
        f_div = random.choice([i for i in range(-8, 9) if i != 0])
        k = random.randint(-5, 5)
        c = random.randint(-20, 20)
        d = c - (f_div * k)
        a = random.randint(-10, 10)
        b = random.randint(-10, 10)
        e = random.randint(-8, 8)
        q = f"|{f(a)}×{f(b)}|+({f(c)}-{f(d)})×{f(e)}÷{f(f_div)}"
        ans = abs(a * b) + (c - d) * e // f_div
    return {
        'question_text': f"計算 {q} 的值。",
        'answer': '',
        'correct_answer': str(int(ans)),
        'mode': 1
    }

def check(user_answer, correct_answer):
    is_correct = str(user_answer).strip() == str(correct_answer).strip()
    return {
        'correct': is_correct,
        'result': '正確' if is_correct else '錯誤'
    }