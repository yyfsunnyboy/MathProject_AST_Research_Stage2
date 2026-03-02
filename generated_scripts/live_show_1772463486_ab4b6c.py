import random

def generate(level=1, **kwargs):
    def f(n):
        return f"({n})" if n < 0 else str(n)
    t = random.randint(1, 4)
    if t == 1:
        a, b, c = [random.randint(-50, 50) for _ in range(3)]
        while a * b * c == 0:
            a, b, c = [random.randint(-50, 50) for _ in range(3)]
        q = f"{f(a)} × {f(b)} × {f(c)}"
        ans = a * b * c
    elif t == 2:
        a, b, c = [random.randint(-100, 100) for _ in range(3)]
        q = f"{f(a)} + {f(b)} - {f(c)}"
        ans = a + b - c
    elif t == 3:
        a, b, c = random.randint(-30, 30), random.randint(-30, 30), random.randint(-100, 100)
        q = f"{f(a)} × {f(b)} + {f(c)}"
        ans = a * b + c
    else:
        b = random.choice([i for i in range(-30, 31) if i != 0])
        tmp = random.randint(-30, 30)
        a, c = b * tmp, random.randint(-100, 100)
        q = f"{f(a)} ÷ {f(b)} - {f(c)}"
        ans = tmp - c
    return {
        'question_text': q,
        'answer': '',
        'correct_answer': str(ans),
        'mode': 1
    }

def check(user_answer, correct_answer):
    c = str(user_answer).strip() == str(correct_answer).strip()
    return {
        'correct': c,
        'result': '正確' if c else '錯誤'
    }