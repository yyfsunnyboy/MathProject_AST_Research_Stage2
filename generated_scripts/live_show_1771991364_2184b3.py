import random

def generate(level=1, **kwargs):
    def f(n):
        return "(" + str(n) + ")" if n < 0 else str(n)
    
    t = random.randint(0, 3)
    if t == 0:
        c = random.choice([i for i in range(-10, 11) if i != 0])
        k = random.randint(-10, 10)
        a = random.randint(-20, 20)
        b = (c * k) - a
        d = random.randint(-10, 10)
        expr = "[ " + f(a) + "+" + f(b) + "]÷" + f(c) + "×" + f(d)
        ans = k * d
    elif t == 1:
        a = random.randint(-15, 15)
        b = random.randint(-10, 10)
        c = random.randint(-15, 15)
        d = random.randint(-10, 10)
        expr = f(a) + "×" + f(b) + "-" + f(c) + "×" + f(d)
        ans = a * b - c * d
    elif t == 2:
        a = random.randint(-50, 50)
        b = random.randint(-20, 20)
        c = random.randint(-20, 20)
        d = random.randint(-8, 8)
        expr = f(a) + "-(" + f(b) + "+" + f(c) + ")×" + f(d)
        ans = a - (b + c) * d
    else:
        div = random.choice([i for i in range(-12, 13) if i != 0])
        m = random.randint(-10, 10)
        dvd = div * m
        a = random.randint(-40, 40)
        expr = f(a) + "+" + f(dvd) + "÷" + f(div)
        ans = a + m
        
    return {
        'question_text': "計算 " + expr + " 的值。",
        'answer': '',
        'correct_answer': str(int(ans)),
        'mode': 1
    }

def check(user_answer, correct_answer):
    is_correct = str(user_answer).strip() == str(correct_answer).strip()
    return {
        'correct': is_correct,
        'result': '正確' if is_correct else '錯誤'
    }