import random

def generate(level=1, **kwargs):
    a = random.randint(-30, 30)
    b = random.randint(-30, 30)
    divisors = [i for i in range(-20, 21) if i != 0 and (a + b) % i == 0]
    c = random.choice(divisors) if divisors else 1
    d = random.randint(-10, 10)
    e = random.randint(-12, 12)
    f = random.randint(-12, 12)
    g = random.randint(-50, 50)
    ans = ((a + b) // c) * d + abs(e * f + g)
    def p(n):
        return f"({n})" if n < 0 else str(n)
    def op_s(n):
        return str(n) if n < 0 else f"+{n}"
    expr = f"[{p(a)}+{p(b)}]÷{p(c)}×{p(d)}+|{p(e)}×{p(f)}{op_s(g)}|"
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