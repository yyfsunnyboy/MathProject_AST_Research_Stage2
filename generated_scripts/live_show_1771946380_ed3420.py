import random

def generate(level=1, **kwargs):
    def f(n):
        return f"({n})" if n < 0 else str(n)
    
    t = random.randint(1, 4)
    if t == 1:
        a, b, c = random.randint(-20, 20), random.randint(-20, 20), random.randint(-20, 20)
        txt, val = f"{f(a)}×{f(b)}+{f(c)}", a * b + c
    elif t == 2:
        c_val = random.choice([i for i in range(-12, 13) if i != 0])
        res_inner = random.randint(-10, 10)
        sum_ab = c_val * res_inner
        a = random.randint(-20, 20)
        b = sum_ab - a
        d = random.randint(-10, 10)
        txt, val = f"[{f(a)}+{f(b)}]÷{f(c_val)}×{f(d)}", res_inner * d
    elif t == 3:
        a, b, c = random.randint(-15, 15), random.randint(-15, 15), random.randint(-15, 15)
        txt, val = f"{f(a)}-{f(b)}×{f(c)}", a - (b * c)
    else:
        d_val = random.choice([i for i in range(-10, 11) if i != 0])
        res_div = random.randint(-10, 10)
        c_val = d_val * res_div
        a, b = random.randint(-12, 12), random.randint(-12, 12)
        txt, val = f"{f(a)}×{f(b)}-{f(c_val)}÷{f(d_val)}", (a * b) - res_div
        
    return {
        'question_text': f"計算 {txt} 的值。",
        'answer': '',
        'correct_answer': str(val),
        'mode': 1
    }

def check(user_answer, correct_answer):
    is_correct = str(user_answer).strip() == str(correct_answer).strip()
    return {
        'correct': is_correct,
        'result': '正確' if is_correct else '錯誤'
    }