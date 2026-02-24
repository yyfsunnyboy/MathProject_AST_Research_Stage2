import random

def generate(level=1, **kwargs):
    def p(n):
        return f"({n})" if n < 0 else str(n)
    
    c = random.choice([i for i in range(-12, 13) if i != 0])
    q_val = random.randint(-10, 10)
    target = c * q_val
    a = random.randint(-30, 30)
    b = target - a
    d = random.randint(-10, 10)
    
    e = random.choice([i for i in range(-10, 11) if i != 0])
    f_val = random.choice([i for i in range(-10, 11) if i != 0])
    g = random.choice([i for i in range(-20, 21) if i != 0])
    
    v1 = q_val * d
    v2 = abs(e * f_val + g)
    
    op = random.choice(['+', '-'])
    ans = v1 + v2 if op == '+' else v1 - v2
    
    s1 = f"[{p(a)}+{p(b)}]÷{p(c)}×{p(d)}"
    
    term_e = str(e) if e > 0 else f"({e})"
    if g < 0:
        s2 = f"|{term_e}×{p(f_val)}-{abs(g)}|"
    else:
        s2 = f"|{term_e}×{p(f_val)}+{g}|"
        
    return {
        'question_text': f"計算 {s1}{op}{s2} 的值。",
        'answer': '',
        'correct_answer': str(ans),
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        is_correct = int(float(user_answer)) == int(correct_answer)
    except:
        is_correct = False
    return {
        'correct': is_correct,
        'result': '正確' if is_correct else '錯誤'
    }