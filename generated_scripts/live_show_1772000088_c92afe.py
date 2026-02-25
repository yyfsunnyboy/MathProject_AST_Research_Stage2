import random

def generate(level=1, **kwargs):
    def f(n):
        return f"({n})" if n < 0 else str(n)
    
    t = random.randint(1, 4)
    if t == 1:
        a, b, c, d = random.randint(-12, 12), random.randint(-12, 12), random.randint(-12, 12), random.randint(-12, 12)
        ans = a * b - c * d
        text = f"計算 {f(a)} × {f(b)} - {f(c)} × {f(d)} 的值。"
    elif t == 2:
        a, b, c, d = random.randint(-10, 10), random.randint(-10, 10), random.randint(-10, 10), random.randint(-10, 10)
        ans = a * (b + c - d)
        text = f"計算 {f(a)} × [{f(b)} + {f(c)} - {f(d)}] 的值。"
    elif t == 3:
        b, c, d = random.randint(-10, 10), random.randint(-10, 10), random.randint(-20, 20)
        denom = b * c - d
        while denom == 0:
            b, c, d = random.randint(-10, 10), random.randint(-10, 10), random.randint(-20, 20)
            denom = b * c - d
        ans_val = random.randint(-15, 15)
        a = ans_val * denom
        ans = ans_val
        text = f"計算 {f(a)} ÷ [{f(b)} × {f(c)} - {f(d)}] 的值。"
    else:
        a, b, c, d = random.randint(-20, 20), random.randint(-10, 10), random.randint(-10, 10), random.randint(-20, 20)
        denom = c + d
        while denom == 0:
            c, d = random.randint(-10, 10), random.randint(-20, 20)
            denom = c + d
        ans_val = random.randint(-15, 15)
        b_val = ans_val * denom
        ans = a - b_val
        text = f"計算 {f(a)} - {f(b_val)} ÷ [{f(c)} + {f(d)}] 的值。"
        
    return {
        'question_text': text,
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