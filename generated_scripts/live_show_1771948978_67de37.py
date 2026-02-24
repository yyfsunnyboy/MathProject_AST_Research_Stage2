import random

def generate(level=1, **kwargs):
    def f(n):
        return f"({n})" if n < 0 else str(n)
    t = random.randint(1, 4)
    if t == 1:
        c = random.choice([i for i in range(-12, 13) if i != 0])
        q = random.randint(-12, 12)
        s = c * q
        a = random.randint(-20, 20)
        b = s - a
        d = random.randint(-10, 10)
        txt = f"[ {f(a)}+{f(b)} ]÷{f(c)}×{f(d)}"
        res = q * d
    elif t == 2:
        a = random.randint(-10, 10)
        b = random.randint(-15, 15)
        c = random.randint(-15, 15)
        d = random.randint(-20, 20)
        txt = f"{f(a)}×[ {f(b)}-{f(c)} ]+{f(d)}"
        res = a * (b - c) + d
    elif t == 3:
        a = random.randint(-12, 12)
        b = random.randint(-12, 12)
        c = random.randint(-12, 12)
        d = random.randint(-12, 12)
        txt = f"[ {f(a)}+{f(b)} ]×[ {f(c)}-{f(d)} ]"
        res = (a + b) * (c - d)
    else:
        d = random.choice([i for i in range(-10, 11) if i != 0])
        q = random.randint(-12, 12)
        s = d * q
        b = random.randint(-20, 20)
        c = s - b
        a = random.randint(-20, 20)
        txt = f"{f(a)}-[ {f(b)}+{f(c)} ]÷{f(d)}"
        res = a - q
    return {
        'question_text': f"計算 {txt} 的值。",
        'answer': '',
        'correct_answer': str(int(res)),
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        is_correct = int(user_answer) == int(correct_answer)
    except:
        is_correct = False
    return {
        'correct': is_correct,
        'result': '正確' if is_correct else '錯誤'
    }