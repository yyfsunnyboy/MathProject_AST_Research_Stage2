import random

def generate(level=1, **kwargs):
    def fmt(n):
        return f"({n})" if n < 0 else str(n)
    case = random.randint(0, 3)
    if case == 0:
        a, b = random.randint(-12, 12), random.randint(-12, 12)
        q, d = random.randint(-12, 12), random.choice([i for i in range(-12, 13) if i != 0])
        c, op = q * d, random.choice(['+', '-'])
        text = f"{fmt(a)}×{fmt(b)}{op}{fmt(c)}÷{fmt(d)}"
        ans = a * b + q if op == '+' else a * b - q
    elif case == 1:
        a, b, c = random.randint(-20, 20), random.randint(-20, 20), random.randint(-10, 10)
        text = f"({fmt(a)}+{fmt(b)})×{fmt(c)}"
        ans = (a + b) * c
    elif case == 2:
        a, b, c = random.randint(-50, 50), random.randint(-12, 12), random.randint(-12, 12)
        text = f"{fmt(a)}-{fmt(b)}×{fmt(c)}"
        ans = a - (b * c)
    else:
        q1, d1 = random.randint(-12, 12), random.choice([i for i in range(-12, 13) if i != 0])
        q2, d2 = random.randint(-12, 12), random.choice([i for i in range(-12, 13) if i != 0])
        text = f"{fmt(q1*d1)}÷{fmt(d1)}+{fmt(q2*d2)}÷{fmt(d2)}"
        ans = q1 + q2
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