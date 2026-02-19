import random

def generate(level=1, **kwargs):
    def p(n):
        return f"({n})" if n < 0 else str(n)
    
    c = random.choice([i for i in range(-12, 13) if i != 0])
    k = random.randint(-10, 10)
    sum_ab = c * k
    a = random.randint(-30, 30)
    b = sum_ab - a
    d = random.randint(-10, 10)
    e = random.randint(-10, 10)
    f = random.randint(-10, 10)
    g = random.randint(-20, 20)
    op = random.choice(['+', '-'])
    
    g_str = f"+{p(g)}" if g >= 0 else f"-{abs(g)}"
    
    part1_val = k * d
    part2_val = abs(e * f + g)
    
    if op == '+':
        res = part1_val + part2_val
    else:
        res = part1_val - part2_val
        
    q_text = f"計算 [{p(a)}+{p(b)}]÷{p(c)}×{p(d)}{op}|{p(e)}×{p(f)}{g_str}| 的值。"
    
    return {
        'question_text': q_text,
        'answer': '',
        'correct_answer': str(res),
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {
        'correct': correct,
        'result': '正確' if correct else '錯誤'
    }