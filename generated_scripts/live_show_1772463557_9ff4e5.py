import random

def generate(level=1, **kwargs):
    def f(n):
        return f"({n})" if n < 0 else str(n)
    
    t = random.randint(1, 4)
    if t == 1:
        a = random.randint(-12, 12)
        b = random.randint(-12, 12)
        c = random.randint(-20, 20)
        res = a * b + c
        q = f"{f(a)} \\times {f(b)} + {f(c)}"
    elif t == 2:
        b = random.randint(-10, 10)
        if b == 0: b = 1
        a = random.randint(-10, 10)
        dividend = a * b
        c = random.randint(-15, 15)
        res = a - c
        q = f"{f(dividend)} \\div {f(b)} - {f(c)}"
    elif t == 3:
        a = random.randint(-10, 10)
        b = random.randint(-10, 10)
        c = random.randint(-10, 10)
        d = random.randint(-10, 10)
        res = (a + b) * (c - d)
        q = f"({f(a)} + {f(b)}) \\times ({f(c)} - {f(d)})"
    else:
        a = random.randint(-8, 8)
        if a == 0: a = 1
        b = random.randint(-15, 15)
        c = random.randint(-8, 8)
        d = random.randint(-8, 8)
        res = a * (b - (c * d))
        q = f"{f(a)} \\times [{f(b)} - {f(c)} \\times {f(d)}]"
        
    return {
        'question_text': q,
        'answer': '',
        'correct_answer': str(res),
        'mode': 1
    }

def check(user_answer, correct_answer):
    is_correct = str(user_answer).strip() == str(correct_answer).strip()
    return {
        'correct': is_correct,
        'result': '正確' if is_correct else '錯誤'
    }