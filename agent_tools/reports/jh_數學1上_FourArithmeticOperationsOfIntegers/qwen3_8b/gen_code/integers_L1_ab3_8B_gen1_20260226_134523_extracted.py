import random
import math

def generate(level=1, **kwargs):
    if level == 1:
        r_min, r_max = -20, 20
        div_max = 10
    elif level == 2:
        r_min, r_max = -50, 50
        div_max = 20
    else:
        r_min, r_max = -100, 100
        div_max = 30
        
    def rand_nz(a, b):
        choices = [x for x in range(a, b+1) if x != 0 and x not in [1, -1]]
        if not choices: return 2
        return random.choice(choices)

    def fmt(n):
        return f"({n})" if n < 0 else str(n)

    if level == 1:
        op = random.choice(['*', '/'])
        if op == '*':
            a = rand_nz(-15, 15)
            b = rand_nz(-10, 10)
            question_text = f"計算 $${fmt(a)} \\times {fmt(b)}$$ 的值。"
            ans = a * b
        else:
            b = rand_nz(-15, 15)
            ans = rand_nz(-10, 10)
            a = b * ans
            question_text = f"計算 $${fmt(a)} \\div {fmt(b)}$$ 的值。"
            
    elif level == 2:
        b = rand_nz(-15, 15)
        temp_ans = rand_nz(-15, 15)
        a = b * temp_ans
        c = rand_nz(-10, 10)
        
        if random.choice([True, False]):
            question_text = f"計算 $${fmt(a)} \\div {fmt(b)} \\times {fmt(c)}$$ 的值。"
            ans = (a // b) * c
        else:
            c2 = rand_nz(-15, 15)
            q = rand_nz(-5, 5)
            b2 = c2 * q
            a2 = rand_nz(-10, 10)
            question_text = f"計算 $${fmt(a2)} \\times {fmt(b2)} \\div {fmt(c2)}$$ 的值。"
            ans = a2 * (b2 // c2)

    else:
        if random.choice([True, False]):
            a = rand_nz(-10, 10)
            b = rand_nz(-10, 10)
            d = rand_nz(-15, 15)
            q = rand_nz(-10, 10)
            c = d * q
            question_text = f"計算 $${fmt(a)} \\times {fmt(b)} + {fmt(c)} \\div {fmt(d)}$$ 的值。"
            ans = a * b + (c // d)
        else:
            a = rand_nz(-20, 20)
            c = rand_nz(-15, 15)
            q = rand_nz(-10, 10)
            b = c * q
            d = rand_nz(-10, 10)
            question_text = f"計算 $${fmt(a)} - {fmt(b)} \\div {fmt(c)} \\times {fmt(d)}$$ 的值。"
            ans = a - (b // c) * d

    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': str(int(ans)),
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        if str(user_answer).strip() == str(correct_answer).strip():
            return {'correct': True, 'result': '正確'}
        if abs(float(user_answer) - float(correct_answer)) < 1e-6:
            return {'correct': True, 'result': '正確'}
    except:
        pass
    return {'correct': False, 'result': '錯誤'}