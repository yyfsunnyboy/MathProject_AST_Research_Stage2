import random
from fractions import Fraction

def generate(level=1, **kwargs):
    if level == 1:
        int_range = (-10, 10)
        frac_range = (1, 8)
    elif level == 2:
        int_range = (-20, 20)
        frac_range = (1, 15)
    else:
        int_range = (-50, 50)
        frac_range = (1, 25)

    def get_frac():
        n = random.randint(1, frac_range[1])
        d = random.randint(2, frac_range[1])
        return Fraction(n, d)

    def get_signed_frac():
        n = random.choice([-1, 1]) * random.randint(1, frac_range[1])
        d = random.randint(2, frac_range[1])
        return Fraction(n, d)

    if level == 1:
        a = random.randint(int_range[0], int_range[1])
        b = random.randint(1, 10)
        f1 = get_frac()
        f2 = get_signed_frac()
        f3 = get_signed_frac()
        c = random.randint(1, 5)
        
        part1 = (a + b) * f1
        part2 = f2
        part3 = abs(c * f3 - random.randint(1, 5))
        
        res = (part1 / part2) + part3
        
        expr = f"\\left[({a} + {b}) \\times {to_latex(f1)}\\right] \\div {fmt_num(f2)} + \\left|{c} \\times {to_latex(f3)} - {random.randint(1, 5)}\\right|"
        
    elif level == 2:
        f1 = get_signed_frac()
        f2 = get_frac()
        f3 = get_frac()
        f4 = get_signed_frac()
        
        nested_top = f1 + f2
        nested_bottom = f3
        nested_val = nested_top / nested_bottom
        
        part1 = nested_val * random.randint(2, 5)
        part2 = get_signed_frac()
        part3 = abs(f4 - random.randint(1, 10))
        
        res = (part1 / part2) + part3
        
        nested_latex = f"\\frac{{{to_latex(f1)} + {to_latex(f2)}}}{{{to_latex(f3)}}}"
        expr = f"\\left[{nested_latex} \\times {random.randint(2, 5)}\\right] \\div {fmt_num(part2)} + \\left|{to_latex(f4)} - {random.randint(1, 10)}\\right|"
        
    else:
        f1 = get_signed_frac()
        f2 = get_signed_frac()
        f3 = get_signed_frac()
        f4 = get_signed_frac()
        
        inner_abs = abs(f1 * random.randint(2, 4) - f2)
        outer_abs = abs(inner_abs / f3 + f4)
        
        res = outer_abs
        
        expr = f"\\left| \\frac{{\\left| {random.randint(2, 4)} \\times {to_latex(f1)} - {to_latex(f2)} \\right|}}{{{to_latex(f3)}}} + {to_latex(f4)} \\right|"

    question_text = f"計算 $$   {expr}   $$ 的值。"
    
    if res.denominator == 1:
        correct_answer = str(res.numerator)
    else:
        correct_answer = f"{res.numerator}/{res.denominator}"
        
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        ua_str = str(user_answer).strip()
        ca_str = str(correct_answer).strip()
        
        if ua_str == ca_str:
            return {'correct': True, 'result': '正確'}
        
        if '/' in ua_str:
            ua_parts = ua_str.split('/')
            ua = Fraction(int(ua_parts[0]), int(ua_parts[1]))
        else:
            ua = Fraction(ua_str)
            
        if '/' in ca_str:
            ca_parts = ca_str.split('/')
            ca = Fraction(int(ca_parts[0]), int(ca_parts[1]))
        else:
            ca = Fraction(ca_str)
            
        if ua == ca:
            return {'correct': True, 'result': '正確'}
        return {'correct': False, 'result': '錯誤'}
    except:
        return {'correct': False, 'result': '錯誤'}