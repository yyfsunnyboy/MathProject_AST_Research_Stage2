import random
from fractions import Fraction

def generate(level=1, **kwargs):
    def fmt(f):
        s = str(f)
        return "(" + s + ")" if f < 0 else s
    def get_frac():
        n = random.choice([i for i in range(-12, 13) if i != 0])
        d = random.randint(1, 12)
        return Fraction(n, d)
    ops = ['+', '-', '*', '/']
    syms = {'+': '+', '-': '−', '*': '×', '/': '÷'}
    f1 = get_frac()
    f2 = get_frac()
    if level == 1:
        op = random.choice(ops)
        q_text = fmt(f1) + " " + syms[op] + " " + fmt(f2)
        if op == '+': ans = f1 + f2
        elif op == '-': ans = f1 - f2
        elif op == '*': ans = f1 * f2
        else: ans = f1 / f2
    else:
        f3 = get_frac()
        op1 = random.choice(ops)
        op2 = random.choice(ops)
        q_text = fmt(f1) + " " + syms[op1] + " " + fmt(f2) + " " + syms[op2] + " " + fmt(f3)
        p1 = 2 if op1 in ['*', '/'] else 1
        p2 = 2 if op2 in ['*', '/'] else 1
        if p2 > p1:
            if op2 == '+': v = f2 + f3
            elif op2 == '-': v = f2 - f3
            elif op2 == '*': v = f2 * f3
            else: v = f2 / f3
            if op1 == '+': ans = f1 + v
            elif op1 == '-': ans = f1 - v
            elif op1 == '*': ans = f1 * v
            else: ans = f1 / v
        else:
            if op1 == '+': v = f1 + f2
            elif op1 == '-': v = f1 - f2
            elif op1 == '*': v = f1 * f2
            else: v = f1 / f2
            if op2 == '+': ans = v + f3
            elif op2 == '-': ans = v - f3
            elif op2 == '*': ans = v * f3
            else: ans = v / f3
    return {
        'question_text': q_text,
        'answer': '',
        'correct_answer': str(ans),
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        ua = Fraction(str(user_answer).strip().replace(' ', ''))
        ca = Fraction(str(correct_answer).strip().replace(' ', ''))
        is_correct = (ua == ca)
    except:
        is_correct = str(user_answer).strip() == str(correct_answer).strip()
    return {
        'correct': is_correct,
        'result': '正確' if is_correct else '錯誤'
    }