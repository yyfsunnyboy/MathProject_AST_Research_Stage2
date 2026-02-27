import random

def generate(level=1, **kwargs):
    def f(n):
        return f"({n})" if n < 0 else str(n)
    
    ops_md = ['×', '÷']
    ops_as = ['+', '-']
    
    o1 = random.choice(ops_md)
    o2 = random.choice(ops_as)
    o3 = random.choice(ops_md)
    
    if o1 == '×':
        a = random.randint(-15, 15)
        b = random.randint(-15, 15)
        r1 = a * b
    else:
        b = random.choice([i for i in range(-15, 16) if i != 0])
        r1 = random.randint(-15, 15)
        a = b * r1
        
    if o3 == '×':
        c = random.randint(-15, 15)
        d = random.randint(-15, 15)
        r2 = c * d
    else:
        d = random.choice([i for i in range(-15, 16) if i != 0])
        r2 = random.randint(-15, 15)
        c = d * r2
        
    if o2 == '+':
        ans = r1 + r2
    else:
        ans = r1 - r2
        
    question = f"{f(a)} {o1} {f(b)} {o2} {f(c)} {o3} {f(d)} ="
    
    return {
        'question_text': question,
        'answer': '',
        'correct_answer': str(ans),
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        is_correct = int(user_answer) == int(correct_answer)
    except:
        is_correct = False
    return {
        'correct': is_correct,
        'result': '正確' if is_correct else '錯誤'
    }