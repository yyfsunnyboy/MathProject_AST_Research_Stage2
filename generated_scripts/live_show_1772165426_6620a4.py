import random

def generate(level=1, **kwargs):
    def f(n):
        return f"({n})" if n < 0 else str(n)
    
    t = random.randint(1, 5)
    if t == 1:
        a, b, c = random.randint(-15, 15), random.randint(-15, 15), random.randint(-30, 30)
        q = f"{f(a)} + {f(b)} × {f(c)}"
        ans = a + b * c
    elif t == 2:
        a, b, c = random.randint(-20, 20), random.randint(-20, 20), random.randint(-15, 15)
        q = f"[ {f(a)} - {f(b)} ] × {f(c)}"
        ans = (a - b) * c
    elif t == 3:
        res = random.randint(-15, 15)
        b, c = random.randint(-10, 10), random.randint(-10, 10)
        den = b + c
        if den == 0: 
            den, b = 1, 1 - c
        a = den * res
        q = f"{f(a)} ÷ [ {f(b)} + {f(c)} ]"
        ans = res
    elif t == 4:
        a, b = random.randint(-12, 12), random.randint(-12, 12)
        res2 = random.randint(-10, 10)
        d = random.randint(-10, 10)
        if d == 0: d = 1
        c = d * res2
        q = f"{f(a)} × {f(b)} + {f(c)} ÷ {f(d)}"
        ans = a * b + res2
    else:
        res = random.randint(-10, 10)
        b, c, d = random.randint(-5, 5), random.randint(-5, 5), random.randint(-10, 10)
        den = b * c + d
        if den == 0: 
            den, d = 1, 1 - b * c
        a = den * res
        q = f"{f(a)} ÷ [ {f(b)} × {f(c)} + {f(d)} ]"
        ans = res

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