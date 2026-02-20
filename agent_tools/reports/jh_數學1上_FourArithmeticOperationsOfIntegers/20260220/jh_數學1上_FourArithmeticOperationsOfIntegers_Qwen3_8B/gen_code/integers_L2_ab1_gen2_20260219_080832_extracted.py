import random
import math

def generate(level=1, **kwargs):
    def generate_bracket():
        a = random.randint(-20, 20)
        b = random.randint(-20, 20)
        op = random.choice(['+', '-'])
        return f'[{a}{op}{b}]'
    
    def generate_abs():
        a = random.randint(-10, 10)
        b = random.randint(-10, 10)
        op = random.choice(['×', '÷'])
        return f'|{a}{op}{b}|'
    
    expr_parts = []
    expr_parts.append(generate_bracket())
    expr_parts.append(generate_abs())
    
    ops = ['÷', '×', '+', '-']
    for _ in range(3):
        expr_parts.append(random.choice(ops))
    
    expr = '÷'.join(expr_parts)
    expr = expr.replace('÷', '÷').replace('×', '×').replace('+', '+').replace('-', '−')
    
    def calculate(expr):
        expr = expr.replace('÷', '/').replace('×', '*').replace('−', '-').replace('+', '+')
        expr = expr.replace('|', '').replace('|', '')
        return str(eval(expr))
    
    correct_answer = calculate(expr)
    return {
        'question_text': f'計算 {expr} 的值。',
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        user_val = int(user_answer)
        correct_val = int(correct_answer)
        return {'correct': user_val == correct_val, 'result': '正確' if user_val == correct_val else '錯誤'}
    except:
        return {'correct': False, 'result': '錯誤'}