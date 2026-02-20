import random

def generate(level=1, **kwargs):
    def f(n, p=True):
        return f"({n})" if n < 0 and p else str(n)
    
    t = random.randint(1, 3)
    if t == 1:
        a = random.randint(-30, 30)
        b = random.randint(-30, 30)
        sum_ab = a + b
        divs = [i for i in range(-20, 21) if i != 0 and sum_ab % i == 0]
        c = random.choice(divs)
        d = random.randint(-10, 10)
        e = random.randint(-10, 10)
        g = random.randint(-10, 10)
        h = random.randint(-20, 20)
        q = f"[{f(a)}+{f(b)}]÷{f(c)}×{f(d)}+|{f(e,0)}×{f(g)}-{f(h,0)}|"
        ans = (sum_ab // c) * d + abs(e * g - h)
    elif t == 2:
        a = random.randint(-12, 12)
        b = random.randint(-20, 20)
        c = random.randint(-15, 15)
        d = random.randint(-15, 15)
        inner = b - (c + d)
        prod = a * inner
        divs = [i for i in range(-12, 13) if i != 0 and prod % i == 0]
        e = random.choice(divs)
        g = random.randint(-20, 20)
        h = random.randint(-20, 20)
        q = f"{f(a)}×[{f(b)}-({f(c)}+{f(d)})]÷{f(e)}-|{f(g,0)}+{f(h,0)}|"
        ans = (prod // e) - abs(g + h)
    else:
        a = random.randint(-10, 10)
        b = random.randint(-10, 10)
        c = random.randint(-25, 25)
        d = random.randint(-10, 10)
        e = random.randint(-15, 15)
        g = random.randint(-15, 15)
        inner = d * (e - g)
        divs = [i for i in range(-10, 11) if i != 0 and inner % i == 0]
        h = random.choice(divs)
        q = f"|{f(a,0)}×{f(b)}+{f(c,0)}|-[{f(d)}×({f(e)}-{f(g)})]÷{f(h)}"
        ans = abs(a * b + c) - (inner // h)
    
    return {
        'question_text': f"計算 {q} 的值。",
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