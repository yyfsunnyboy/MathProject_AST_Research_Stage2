import random

def generate(level=1, **kwargs):
    def p(n):
        return f"({n})" if n < 0 else str(n)
    
    c = random.choice([i for i in range(-12, 13) if i != 0])
    k = random.randint(-10, 10)
    s = c * k
    a = random.randint(-30, 30)
    b = s - a
    d = random.randint(-10, 10)
    
    e = random.randint(-10, 10)
    f = random.randint(-10, 10)
    g = random.choice([i for i in range(-30, 31) if i != 0])
    
    op = random.choice(['+', '-'])
    
    expr = f"[{p(a)}+{p(b)}]÷{p(c)}×{p(d)}{op}|{e}×{p(f)}{'+' if g > 0 else ''}{g}|"
    
    v1 = (a + b) // c * d
    v2 = abs(e * f + g)
    ans = v1 + v2 if op == '+' else v1 - v2
    
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