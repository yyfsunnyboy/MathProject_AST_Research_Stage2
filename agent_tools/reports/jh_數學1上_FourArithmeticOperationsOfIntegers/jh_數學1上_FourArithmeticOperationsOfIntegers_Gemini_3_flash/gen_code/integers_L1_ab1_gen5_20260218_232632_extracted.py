import random

def generate(level=1, **kwargs):
    def fmt(n):
        return f"({n})" if n < 0 else str(n)
    
    t = random.randint(1, 3)
    if t == 1:
        c = random.choice([i for i in range(-10, 11) if i != 0])
        sum_ab = c * random.randint(-10, 10)
        a = random.randint(-20, 20)
        b = sum_ab - a
        d = random.randint(-10, 10)
        e = random.randint(2, 10)
        f = random.randint(-10, -2)
        g = random.choice([i for i in range(-15, 16) if i != 0])
        q = f"[{fmt(a)}+{fmt(b)}]÷{fmt(c)}×{fmt(d)}+|{fmt(e)}×{fmt(f)}{g if g < 0 else '+' + str(g)}|"
        ans = (a + b) // c * d + abs(e * f + g)
    elif t == 2:
        f = random.choice([i for i in range(-10, 11) if i != 0])
        sum_de = f * random.randint(-10, 10)
        d = random.randint(-20, 20)
        e = sum_de - d
        a = random.randint(-10, 10)
        b = random.randint(-20, 20)
        c = random.randint(-20, 20)
        q = f"{fmt(a)}×({fmt(b)}-{fmt(c)})-|{fmt(d)}{e if e < 0 else '+' + str(e)}|÷{fmt(f)}"
        ans = a * (b - c) - abs(d + e) // f
    else:
        f = random.choice([i for i in range(-10, 11) if i != 0])
        diff_cd = f * random.randint(-5, 5)
        c = random.randint(-20, 20)
        d = c - diff_cd
        a = random.randint(-10, 10)
        b = random.randint(-10, 10)
        e = random.randint(-10, 10)
        q = f"|{fmt(a)}×{fmt(b)}|+({fmt(c)}-{fmt(d)})×{fmt(e)}÷{fmt(f)}"
        ans = abs(a * b) + (c - d) * e // f
        
    return {
        'question_text': f"計算 {q} 的值。",
        'answer': '',
        'correct_answer': str(int(ans)),
        'mode': 1
    }

def check(user_answer, correct_answer):
    res = str(user_answer).strip() == str(correct_answer).strip()
    return {
        'correct': res,
        'result': '正確' if res else '錯誤'
    }