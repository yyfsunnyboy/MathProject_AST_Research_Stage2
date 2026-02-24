import random

def generate(level=1, **kwargs):
    def f(n):
        return f"({n})" if n < 0 else str(n)
    
    c = random.choice([i for i in range(-10, 11) if i != 0])
    r_in = random.randint(-10, 10)
    s_ab = c * r_in
    a = random.randint(-25, 25)
    b = s_ab - a
    d = random.randint(-10, 10)
    p1_v = r_in * d
    p1_t = f"[{f(a)}+{f(b)}]÷{f(c)}×{f(d)}"
    
    e = random.randint(-10, 10)
    g = random.randint(-10, 10)
    h = random.randint(-25, 25)
    p2_v = abs(e * g + h)
    p2_t = f"|{f(e)}×{f(g)}+{f(h)}|"
    
    op = random.choice(['+', '-'])
    if op == '+':
        res = p1_v + p2_v
    else:
        res = p1_v - p2_v
        
    return {
        'question_text': f"計算 {p1_t}{op}{p2_t} 的值。",
        'answer': '',
        'correct_answer': str(res),
        'mode': 1
    }

def check(user_answer, correct_answer):
    is_correct = str(user_answer).strip() == str(correct_answer).strip()
    return {
        'correct': is_correct,
        'result': '正確' if is_correct else '錯誤'
    }