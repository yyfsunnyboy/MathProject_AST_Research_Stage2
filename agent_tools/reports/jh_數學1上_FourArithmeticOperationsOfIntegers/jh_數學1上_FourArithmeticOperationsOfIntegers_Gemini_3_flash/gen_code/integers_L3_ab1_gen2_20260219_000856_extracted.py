import random

def generate(level=1, **kwargs):
    def p(n):
        return f"({n})" if n < 0 else str(n)
    
    t = random.randint(1, 3)
    if t == 1:
        a = random.randint(-30, -2)
        b = random.randint(-30, -2)
        s = a + b
        divs = [i for i in range(-15, 16) if i != 0 and s % i == 0]
        c = random.choice(divs)
        d = random.randint(2, 10)
        e = random.randint(2, 12)
        f = random.randint(-10, -2)
        g = random.randint(-20, -2)
        val = (s // c) * d + abs(e * f + g)
        q = f"[{p(a)}+{p(b)}]÷{p(c)}×{p(d)}+|{p(e)}×{p(f)}+{p(g)}|"
    elif t == 2:
        a = random.randint(-12, 12)
        b = random.randint(-20, 20)
        c = random.randint(-20, 20)
        e = random.choice([i for i in range(-10, 11) if i != 0])
        d = e * random.randint(-8, 8)
        f = random.randint(-30, 30)
        val = a * (b - c) + (d // e) - abs(f)
        q = f"{p(a)}×({p(b)}-{p(c)})+{p(d)}÷{p(e)}-|{p(f)}|"
    else:
        a = random.randint(-10, 10)
        b = random.randint(-10, 10)
        c = random.randint(-20, 20)
        d = random.randint(-15, 15)
        e = random.randint(-15, 15)
        val = abs(a * b + c) - d * e
        q = f"|{p(a)}×{p(b)}+{p(c)}|-{p(d)}×{p(e)}"
        
    return {
        'question_text': f"計算 {q} 的值。",
        'answer': '',
        'correct_answer': str(val),
        'mode': 1
    }

def check(user_answer, correct_answer):
    ua = str(user_answer).strip()
    ca = str(correct_answer).strip()
    is_correct = ua == ca
    return {
        'correct': is_correct,
        'result': '正確' if is_correct else '錯誤'
    }