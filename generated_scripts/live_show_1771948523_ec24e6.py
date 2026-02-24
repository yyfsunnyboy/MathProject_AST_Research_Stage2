import random
import math

def _simplify(n):
    a = 1
    d = 2
    t = n
    while d * d <= t:
        while t % (d * d) == 0:
            a *= d
            t //= (d * d)
        d += 1
    return a, t

def _to_latex(a, b):
    if a == 0:
        return "0"
    if b == 1:
        return str(a)
    res = ""
    if a == -1:
        res = "-"
    elif a != 1:
        res = str(a)
    res += f"\\sqrt{{{b}}}"
    return res

def generate(level=1, **kwargs):
    scale = level if level > 0 else 1
    op = random.choice(['+', '-', '*', '/'])
    
    if op in ['+', '-']:
        k = random.choice([2, 3, 5, 6, 7, 10, 11, 13, 14, 15])
        m1 = random.randint(1, 1 + scale)
        m2 = random.randint(1, 1 + scale)
        c1 = random.randint(1, 3 + scale)
        c2 = random.randint(1, 3 + scale)
        n1 = k * m1 * m1
        n2 = k * m2 * m2
        
        t1 = f"\\sqrt{{{n1}}}" if c1 == 1 else f"{c1}\\sqrt{{{n1}}}"
        t2 = f"\\sqrt{{{n2}}}" if c2 == 1 else f"{c2}\\sqrt{{{n2}}}"
        
        if op == '+':
            q = f"${t1} + {t2}$"
            ans_val = c1 * m1 + c2 * m2
        else:
            q = f"${t1} - {t2}$"
            ans_val = c1 * m1 - c2 * m2
        correct_ans = _to_latex(ans_val, k)
        
    elif op == '*':
        n1 = random.randint(2, 5 * scale + 5)
        n2 = random.randint(2, 5 * scale + 5)
        q = f"$\\sqrt{{{n1}}} \\times \\sqrt{{{n2}}}$"
        a, b = _simplify(n1 * n2)
        correct_ans = _to_latex(a, b)
        
    else:
        res_val = random.randint(2, 4 + scale)
        n2 = random.randint(2, 10 + scale)
        n1 = n2 * res_val * res_val
        q = f"$\\sqrt{{{n1}}} \\div \\sqrt{{{n2}}}$"
        correct_ans = str(res_val)
        
    return {
        'question_text': q,
        'answer': '',
        'correct_answer': correct_ans,
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}