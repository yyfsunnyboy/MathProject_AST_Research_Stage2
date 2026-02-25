import random
from fractions import Fraction

def generate(level=1, **kwargs):
    def f_str(f):
        s = str(f)
        return f"({s})" if f < 0 else s
    
    def get_f():
        limit = 5 + level * 5
        n = random.randint(-limit, limit)
        d = random.randint(1, limit)
        return Fraction(n, d)
    
    ops = [
        ('+', lambda a, b: a + b, '+'),
        ('-', lambda a, b: a - b, '-'),
        ('*', lambda a, b: a * b, '×'),
        ('/', lambda a, b: a / b, '÷')
    ]
    
    try:
        f1, f2, f3 = get_f(), get_f(), get_f()
        o1_s, o1_f, o1_d = random.choice(ops)
        o2_s, o2_f, o2_d = random.choice(ops)
        
        t = random.randint(1, 3)
        if t == 1:
            q = f"計算 {f_str(f1)} {o1_d} {f_str(f2)} {o2_d} {f_str(f3)} 的值。"
            if o2_s in '*/' and o1_s in '+-':
                ans = o1_f(f1, o2_f(f2, f3))
            else:
                ans = o2_f(o1_f(f1, f2), f3)
        elif t == 2:
            q = f"計算 ({f_str(f1)} {o1_d} {f_str(f2)}) {o2_d} {f_str(f3)} 的值。"
            ans = o2_f(o1_f(f1, f2), f3)
        else:
            q = f"計算 {f_str(f1)} {o1_d} ({f_str(f2)} {o2_d} {f_str(f3)}) 的值。"
            ans = o1_f(f1, o2_f(f2, f3))
            
        return {
            'question_text': q,
            'answer': '',
            'correct_answer': str(ans),
            'mode': 1
        }
    except ZeroDivisionError:
        return generate(level=level, **kwargs)

def check(user_answer, correct_answer):
    try:
        ua = user_answer.replace(' ', '')
        ca = correct_answer.replace(' ', '')
        is_correct = Fraction(ua) == Fraction(ca)
    except:
        is_correct = user_answer.strip() == correct_answer.strip()
    
    return {
        'correct': is_correct,
        'result': '正確' if is_correct else '錯誤'
    }