import random

def generate(level=1, **kwargs):
    def p(n):
        return f"({n})" if n < 0 else str(n)
    
    c = random.randint(2, 9) * random.choice([-1, 1])
    k = random.randint(-9, 9)
    s = c * k
    a = random.randint(-20, 20)
    b = s - a
    d = random.randint(-9, 9)
    e = random.randint(-9, 9)
    f = random.randint(-9, 9)
    g = random.randint(-20, 20)
    op = random.choice(['+', '-'])
    
    expr = f"[{p(a)}+{p(b)}]÷{p(c)}×{p(d)}{op}|{p(e)}×{p(f)}+{p(g)}|"
    
    v1 = k * d
    v2 = abs(e * f + g)
    ans = v1 + v2 if op == '+' else v1 - v2
    
    return {
        'question_text': f"計算 {expr} 的值。",
        'answer': '',
        'correct_answer': str(ans),
        'mode': 1
    }

def check(user_answer, correct_answer):
    ua = str(user_answer).strip()
    ca = str(correct_answer).strip()
    is_correct = ua == ca
    return {
        'correct': is_correct,
        'result': '正確' if is_correct else '錯誤'
    }