import random

def generate(level=1, **kwargs):
    def f(n):
        return f"({n})" if n < 0 else str(n)
    s = {'+': '+', '-': '-', '*': '×', '/': '÷'}
    if level == 1:
        op = random.choice(['+', '-', '*', '/'])
        if op == '+':
            a, b = random.randint(-100, 100), random.randint(-100, 100)
            ans = a + b
        elif op == '-':
            a, b = random.randint(-100, 100), random.randint(-100, 100)
            ans = a - b
        elif op == '*':
            a, b = random.randint(-20, 20), random.randint(-20, 20)
            ans = a * b
        else:
            b = random.choice([i for i in range(-20, 21) if i != 0])
            ans = random.randint(-20, 20)
            a = b * ans
        q = f"{f(a)}{s[op]}{f(b)}"
    else:
        a = random.randint(-50, 50)
        b = random.randint(-50, 50)
        c = random.randint(-50, 50)
        o1 = random.choice(['+', '-', '*'])
        o2 = random.choice(['+', '-', '*'])
        if o1 == '+': v = a + b
        elif o1 == '-': v = a - b
        else: v = a * b
        if o2 == '+': ans = v + c
        elif o2 == '-': ans = v - c
        else: ans = v * c
        q = f"{f(a)}{s[o1]}{f(b)}{s[o2]}{f(c)}"
    return {
        'question_text': q,
        'answer': '',
        'correct_answer': str(ans),
        'mode': 1
    }

def check(user_answer, correct_answer):
    res = str(user_answer).strip() == str(correct_answer).strip()
    return {
        'correct': res,
        'result': '正確' if res else '錯誤'
    }