import random

def generate(level=1, **kwargs):
    def fmt(n):
        return f"({n})" if n < 0 else str(n)
    
    case = random.randint(1, 4)
    if case == 1:
        # (a / b) +/- (c / d)
        b1 = random.choice([i for i in range(-15, 16) if i != 0])
        q1 = random.randint(-15, 15)
        a1 = b1 * q1
        b2 = random.choice([i for i in range(-15, 16) if i != 0])
        q2 = random.randint(-15, 15)
        a2 = b2 * q2
        op = random.choice(['+', '-'])
        ans = q1 + q2 if op == '+' else q1 - q2
        txt = f"{fmt(a1)} ÷ {fmt(b1)} {op} {fmt(a2)} ÷ {fmt(b2)}="
    elif case == 2:
        # a * b +/- c / d
        a1, b1 = random.randint(-12, 12), random.randint(-12, 12)
        b2 = random.choice([i for i in range(-12, 13) if i != 0])
        q2 = random.randint(-12, 12)
        a2 = b2 * q2
        op = random.choice(['+', '-'])
        ans = (a1 * b1) + q2 if op == '+' else (a1 * b1) - q2
        txt = f"{fmt(a1)} × {fmt(b1)} {op} {fmt(a2)} ÷ {fmt(b2)}="
    elif case == 3:
        # (a + b) * c
        a, b, c = random.randint(-20, 20), random.randint(-20, 20), random.randint(-10, 10)
        ans = (a + b) * c
        txt = f"({fmt(a)} + {fmt(b)}) × {fmt(c)}="
    else:
        # a * (b - c)
        a = random.randint(-10, 10)
        b, c = random.randint(-20, 20), random.randint(-20, 20)
        ans = a * (b - c)
        txt = f"{fmt(a)} × ({fmt(b)} - {fmt(c)})="
        
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