import random

def generate(level=1, **kwargs):
    def fmt(n):
        return f"({n})" if n < 0 else str(n)
    
    c = random.choice([i for i in range(-12, 13) if i != 0])
    k = random.randint(-10, 10)
    sum_ab = c * k
    a = random.randint(-30, 30)
    b = sum_ab - a
    d = random.randint(-10, 10)
    
    e = random.randint(-10, 10)
    f = random.randint(-10, 10)
    g = random.randint(-30, 30)
    
    val1 = (sum_ab // c) * d
    val2 = abs(e * f + g)
    ans = val1 + val2
    
    sa = fmt(a)
    sb = fmt(b)
    sc = fmt(c)
    sd = fmt(d)
    se = fmt(e)
    sf = fmt(f)
    
    op_g = "+" if g >= 0 else "-"
    sg_abs = str(abs(g))
    
    expr = f"[{sa}+{sb}]÷{sc}×{sd}+|{se}×{sf}{op_g}{sg_abs}|"
    
    return {
        'question_text': f"計算 {expr} 的值。",
        'answer': '',
        'correct_answer': str(ans),
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        is_correct = str(user_answer).strip() == str(correct_answer).strip()
    except:
        is_correct = False
    return {
        'correct': is_correct,
        'result': '正確' if is_correct else '錯誤'
    }