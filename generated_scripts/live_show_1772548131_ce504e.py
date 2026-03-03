import random

def generate(level=1, **kwargs):
    def f(n):
        return f"({n})" if n < 0 else str(n)
    
    t = random.randint(1, 5)
    if t == 1:
        a, b, c, d, e = [random.randint(-10, 10) for _ in range(5)]
        q = f"{f(a)} × {f(b)} + |{f(c)} × {f(d)} - {f(e)}|"
        ans = a * b + abs(c * d - e)
    elif t == 2:
        a, b, c, d = [random.randint(-12, 12) for _ in range(4)]
        q = f"{f(a)} × ({f(b)} + {f(c)}) - {f(d)}"
        ans = a * (b + c) - d
    elif t == 3:
        e = random.choice([i for i in range(-10, 11) if i != 0])
        res = random.randint(-10, 10)
        d = e * res
        a, b, c = [random.randint(-10, 10) for _ in range(3)]
        q = f"({f(a)} - {f(b)}) × {f(c)} + {f(d)} ÷ {f(e)}"
        ans = (a - b) * c + res
    elif t == 4:
        a, b, c, d, e = [random.randint(-10, 10) for _ in range(5)]
        q = f"|{f(a)} + {f(b)}| × {f(c)} - ({f(d)} + {f(e)})"
        ans = abs(a + b) * c - (d + e)
    else:
        a, b, c = [random.randint(-15, 15) for _ in range(3)]
        q = f"{f(a)} × {f(b)} - {f(c)}"
        ans = a * b - c

    return {
        'question_text': q,
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