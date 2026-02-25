import random

def generate(level=1, **kwargs):
    def f(n):
        return f"({n})" if n < 0 else str(n)
    
    t = random.randint(1, 4)
    if t == 1:
        a, b, c = random.randint(-20, 20), random.randint(-20, 20), random.randint(-10, 10)
        expr = f"{f(a)}×{f(b)}+{f(c)}"
        ans = a * b + c
    elif t == 2:
        a, b = random.randint(-40, 40), random.randint(-40, 40)
        divisor = random.choice([i for i in range(-15, 16) if i != 0])
        res_div = random.randint(-10, 10)
        dividend = divisor * res_div
        expr = f"{f(a)}-{f(b)}+{f(dividend)}÷{f(divisor)}"
        ans = a - b + res_div
    elif t == 3:
        a, b = random.randint(-25, 25), random.randint(-25, 25)
        s = a + b
        factors = [i for i in range(-15, 16) if i != 0 and s % i == 0]
        c = random.choice(factors)
        d = random.randint(-10, 10)
        expr = f"[{f(a)}+{f(b)}]÷{f(c)}×{f(d)}"
        ans = (s // c) * d
    else:
        a, b, c = random.randint(-10, 10), random.randint(-10, 10), random.randint(-10, 10)
        d = random.randint(-30, 30)
        expr = f"{f(d)}-[{f(a)}×{f(b)}+{f(c)}]"
        ans = d - (a * b + c)
        
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