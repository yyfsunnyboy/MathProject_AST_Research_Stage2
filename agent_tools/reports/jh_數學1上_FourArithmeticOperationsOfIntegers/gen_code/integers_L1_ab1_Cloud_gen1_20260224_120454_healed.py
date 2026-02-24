import random

def generate(level=1, **kwargs):
    def f(n):
        return f"({n})" if n < 0 else str(n)
    
    c = random.choice([i for i in range(-10, 11) if i != 0])
    m = random.randint(-8, 8)
    s = c * m
    a = random.randint(-20, 20)
    b = s - a
    d = random.randint(-10, 10)
    e = random.randint(-10, 10)
    g = random.randint(-10, 10)
    h = random.randint(-20, 20)
    
    part1 = f"[{f(a)}+{f(b)}]÷{f(c)}×{f(d)}"
    
    abs_inner_str = f"{f(e)}×{f(g)}"
    if h >= 0:
        abs_inner_str += f"+{h}"
    else:
        abs_inner_str += f"-{abs(h)}"
    
    abs_part = f"|{abs_inner_str}|"
    
    if random.choice([True, False]):
        q = f"{part1}+{abs_part}"
        ans = (s // c) * d + abs(e * g + h)
    else:
        q = f"{part1}-{abs_part}"
        ans = (s // c) * d - abs(e * g + h)
        
    return {
        'question_text': f"計算 {q} 的值。",
        'answer': '',
        'correct_answer': str(int(ans)),
        'mode': 1
    }

def check(user_answer, correct_answer):
    is_correct = str(user_answer).strip() == str(correct_answer).strip()
    return {
        'correct': is_correct,
        'result': '正確' if is_correct else '錯誤'
    }