import random

def generate(level=1, **kwargs):
    def p(n):
        return f"({n})" if n < 0 else str(n)
    def o(n):
        return f"+{n}" if n >= 0 else f"-{abs(n)}"
    
    t = random.randint(1, 3)
    if t == 1:
        a = random.choice([x for x in range(-15, 16) if x != 0])
        b = random.choice([x for x in range(-15, 16) if x != 0])
        c = random.choice([x for x in range(-50, 51) if x != 0])
        ans = a * b + c
        txt = f"計算 {p(a)}×{p(b)}{o(c)} 的值。"
    elif t == 2:
        b = random.choice([x for x in range(-10, 11) if x != 0])
        c = random.choice([x for x in range(-5, 6) if x != 0])
        d = random.choice([x for x in range(-20, 21) if x != 0])
        while b * c + d == 0:
            d = random.choice([x for x in range(-20, 21) if x != 0])
        ans = random.randint(-12, 12)
        a = ans * (b * c + d)
        txt = f"計算 {p(a)}÷[{p(b)}×{p(c)}{o(d)}] 的值。"
    else:
        a = random.randint(-20, 20)
        b = random.choice([x for x in range(-20, 21) if x != 0])
        c = random.choice([x for x in range(-10, 11) if x != 0])
        ans = a - b * c
        txt = f"計算 {p(a)}-{p(b)}×{p(c)} 的值。"
        
    return {
        'question_text': txt,
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