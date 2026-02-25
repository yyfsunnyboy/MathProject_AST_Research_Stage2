import random

def generate(level=1, **kwargs):
    def p(n):
        return f"({n})" if n < 0 else str(n)
    t = random.randint(1, 4)
    if t == 1:
        b = random.randint(-10, 10)
        if b == 0: b = 2
        c = random.randint(-10, 10)
        d = random.randint(-15, 15)
        inner = b * c + d
        if inner == 0: inner = 5
        ans = random.randint(-20, 20)
        a = ans * inner
        op = '+' if d >= 0 else '-'
        q = f"{p(a)}÷[{p(b)}×{p(c)}{op}{abs(d)}]"
    elif t == 2:
        a = random.randint(-20, 20)
        b = random.randint(-15, 15)
        c = random.randint(-15, 15)
        d = random.randint(-10, 10)
        ans = a - (b + c) * d
        op = '+' if c >= 0 else '-'
        q = f"{p(a)}-({p(b)}{op}{abs(c)})×{p(d)}"
    elif t == 3:
        a = random.randint(-15, 15)
        b = random.randint(-15, 15)
        c = random.randint(-10, 10)
        d = random.randint(-10, 10)
        ans = (a - b) * (c + d)
        op1 = '-' if b >= 0 else '+'
        op2 = '+' if d >= 0 else '-'
        q = f"({p(a)}{op1}{abs(b)})×({p(c)}{op2}{abs(d)})"
    else:
        c = random.randint(-10, 10)
        d = random.randint(-10, 10)
        if c == d: d = c + 1
        diff = c - d
        res_div = random.randint(-10, 10)
        b = res_div * diff
        a = random.randint(-20, 20)
        ans = a + res_div
        op = '-' if d >= 0 else '+'
        q = f"{p(a)}+{p(b)}÷({p(c)}{op}{abs(d)})"
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