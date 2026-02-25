import random

def generate(level=1, **kwargs):
    def f(n):
        return f"({n})" if n < 0 else str(n)
    
    r = 10 + level * 5
    mode = random.randint(1, 4)
    if mode == 1:
        a, b, c, d = [random.randint(-r, r) for _ in range(4)]
        ans = a * (b + c) - d
        expr = f"{f(a)}×({f(b)}+{f(c)})-{f(d)}"
    elif mode == 2:
        a, b, c, d = [random.randint(-r, r) for _ in range(4)]
        ans = (a - b) * c + d
        expr = f"({f(a)}-{f(b)})×{f(c)}+{f(d)}"
    elif mode == 3:
        b = random.randint(-r//2, r//2) or 1
        c = random.randint(-r//2, r//2)
        d = random.randint(-r//2, r//2)
        inner = b * (c + d)
        while inner == 0:
            c = random.randint(-r//2, r//2)
            d = random.randint(-r//2, r//2)
            inner = b * (c + d)
        ans = random.randint(-r, r)
        a = inner * ans
        expr = f"{f(a)}÷[{f(b)}×({f(c)}+{f(d)})]"
    else:
        b = random.randint(-r//2, r//2) or 1
        c = random.randint(-r//2, r//2)
        d = random.randint(-r//2, r//2)
        inner = b * c - d
        while inner == 0:
            c = random.randint(-r//2, r//2)
            d = random.randint(-r//2, r//2)
            inner = b * c - d
        ans = random.randint(-r, r)
        a = inner * ans
        expr = f"{f(a)}÷[ ({f(b)}×{f(c)}-{f(d)}) ]"
    
    return {
        'question_text': f"計算 {expr} 的值。",
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