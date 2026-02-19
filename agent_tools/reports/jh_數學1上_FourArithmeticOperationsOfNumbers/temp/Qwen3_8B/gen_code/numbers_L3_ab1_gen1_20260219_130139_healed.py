import random
from fractions import Fraction

def generate(level=1, **kwargs):
    import random
    from fractions import Fraction

    def generate_fraction():
        numerator = random.randint(-10, 10)
        denominator = random.randint(1, 10)
        return f"{numerator}/{denominator}"

    def generate_integer():
        return str(random.randint(-10, 10))

    if level == 1:
        op1 = random.choice(['+', '-', '×', '÷'])
        a = generate_integer()
        b = generate_fraction()
        a_expr = f"({a} {op1} {b})"
        
        b_frac = generate_fraction()
        
        c = generate_fraction()
        d = generate_fraction()
        e = generate_fraction()
        abs_expr = f"|{c} × {d} - {e}|"
        
        question_text = f"計算 [{a_expr}] ÷ {b_frac} + {abs_expr} 的值。"
        
        a_val = Fraction(a.replace('/', '/*').replace(' ', '')) if '/' in a else Fraction(a)
        b_val = Fraction(b.replace('/', '/*'))
        c_val = Fraction(c.replace('/', '/*'))
        d_val = Fraction(d.replace('/', '/*'))
        e_val = Fraction(e.replace('/', '/*'))
        
        if op1 == '+':
            a_result = a_val + b_val
        elif op1 == '-':
            a_result = a_val - b_val
        elif op1 == '×':
            a_result = a_val * b_val
        elif op1 == '÷':
            a_result = a_val / b_val
        
        abs_result = abs(c_val * d_val - e_val)
        total = a_result / b_val + abs_result
        
        correct_answer = str(total).replace('/', '⁄')
        return {
            'question_text': question_text,
            'answer': '',
            'correct_answer': correct_answer,
            'mode': 1
        }

def check(user_answer, correct_answer):
    import re
    user_answer = user_answer.strip()
    correct_answer = correct_answer.strip()
    
    user_parts = re.split(r'[\+\-\×\÷\⁄\|]', user_answer)
    correct_parts = re.split(r'[\+\-\×\÷\⁄\|]', correct_answer)
    
    if len(user_parts) != len(correct_parts):
        return {'correct': False, 'result': '錯誤'}
    
    for u, c in zip(user_parts, correct_parts):
        if not u or not c:
            continue
        try:
            u_val = Fraction(u.replace('⁄', '/'))
            c_val = Fraction(c.replace('⁄', '/'))
            if u_val != c_val:
                return {'correct': False, 'result': '錯誤'}
        except:
            return {'correct': False, 'result': '錯誤'}
    
    return {'correct': True, 'result': '正確'}