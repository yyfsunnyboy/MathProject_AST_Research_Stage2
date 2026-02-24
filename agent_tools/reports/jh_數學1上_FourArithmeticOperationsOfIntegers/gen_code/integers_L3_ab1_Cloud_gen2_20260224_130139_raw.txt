import random

def generate(level=1, **kwargs):
    a = random.randint(-30, 30)
    b = random.randint(-30, 30)
    op1 = random.choice(['+', '-'])
    res1 = a + b if op1 == '+' else a - b
    
    divs = [i for i in range(-15, 16) if i != 0 and res1 % i == 0]
    c = random.choice(divs)
    
    d = random.randint(-10, 10)
    e = random.randint(-10, 10)
    f = random.randint(-10, 10)
    g = random.randint(-30, 30)
    op2 = random.choice(['+', '-'])
    
    res2 = (res1 // c) * d
    res3 = abs(e * f + g) if op2 == '+' else abs(e * f - g)
    correct_val = res2 + res3
    
    def f_str(n):
        return f"({n})" if n < 0 else str(n)
        
    s_a, s_b, s_c, s_d, s_e, s_f, s_g = map(f_str, [a, b, c, d, e, f, g])
    expr = f"[{s_a}{op1}{s_b}]÷{s_c}×{s_d}+|{s_e}×{s_f}{op2}{s_g}|"
    
    return {
        'question_text': f"計算 {expr} 的值。",
        'answer': '',
        'correct_answer': str(correct_val),
        'mode': 1
    }

def check(user_answer, correct_answer):
    is_correct = str(user_answer).strip() == str(correct_answer).strip()
    return {
        'correct': is_correct,
        'result': '正確' if is_correct else '錯誤'
    }