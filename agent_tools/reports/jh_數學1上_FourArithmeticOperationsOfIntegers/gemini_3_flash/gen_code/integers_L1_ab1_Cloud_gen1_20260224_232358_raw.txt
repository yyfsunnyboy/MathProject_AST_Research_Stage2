import random

def generate(level=1, **kwargs):
    c = random.choice([i for i in range(-10, 11) if i != 0])
    m = random.randint(-10, 10)
    s = c * m
    a = random.randint(-20, 20)
    b = s - a
    d = random.randint(-10, 10)
    e = random.randint(-10, 10)
    f = random.randint(-10, 10)
    g = random.choice([i for i in range(-20, 21) if i != 0])
    def p(n):
        return f"({n})" if n < 0 else str(n)
    expr = f"[{p(a)}+{p(b)}]÷{p(c)}×{p(d)}+|{p(e)}×{p(f)}{'+' if g > 0 else ''}{g}|"
    ans = (a + b) // c * d + abs(e * f + g)
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