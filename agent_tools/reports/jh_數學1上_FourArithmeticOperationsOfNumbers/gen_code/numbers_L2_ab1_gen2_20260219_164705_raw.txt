import random
from fractions import Fraction

def generate(level=1, **kwargs):
    ops = ['+', '-', '×', '÷']
    signs = ['+', '-']
    
    # 生成括号内表达式
    a = Fraction(random.randint(1, 10) * random.choice(signs), 1)
    b = Fraction(random.randint(1, 10), random.randint(1, 10))
    c = Fraction(random.randint(1, 10), random.randint(1, 10))
    d = Fraction(random.randint(1, 10) * random.choice(signs), 1)
    e = Fraction(random.randint(1, 10), random.randint(1, 10))
    f = Fraction(random.randint(1, 10), random.randint(1, 10))
    g = Fraction(random.randint(1, 10), 1)
    
    part1 = f"({a}{ops[0]}{b}){ops[2]}{c}"
    part2 = f"{d}{ops[3]}{e}"
    abs_part = f"|{f}{ops[0]}{g}{ops[1]}{h}|"
    
    question_text = f"計算 $[{part1}]÷{part2} + {abs_part}$ 的值。"
    
    # 計算正確答案
    try:
        expr1 = eval(part1.replace('×', '*').replace('÷', '/'))
        expr2 = eval(part2.replace('×', '*').replace('÷', '/'))
        abs_expr = eval(abs_part.replace('×', '*').replace('÷', '/'))
        correct_answer = str(Fraction(expr1 / expr2 + abs_expr).limit_denominator())
    except:
        correct_answer = "0"
    
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        user = Fraction(user_answer)
        correct = Fraction(correct_answer)
        return {'correct': user == correct, 'result': '正確' if user == correct else '錯誤'}
    except:
        return {'correct': False, 'result': '錯誤'}