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
        f_top = get_signed_frac()
        f_bot = Fraction(1, 1) + get_frac()
        nested_f = f_top / f_bot
        
        a = random.randint(int_range[0], int_range[1])
        f1 = get_frac()
        f2 = get_signed_frac()
        
        part1 = (a * f1)
        part2 = nested_f
        part3 = abs(f2 - random.randint(1, 3))
        
        res = (part1 / part2) - part3
        
        nested_latex = f"\\frac{{{to_latex(f_top)}}}" + "{" + f"1 + {to_latex(f_bot-1)}" + "}"
        expr = f"\\left({a} \\times {to_latex(f1)}\\right) \\div \\left({nested_latex}\\right) - \\left|{to_latex(f2)} - {random.randint(1, 3)}\\right|"
        
    else:
        f1 = get_signed_frac()
        f2 = get_signed_frac()
        f3 = get_signed_frac()
        f4 = get_signed_frac()
        
        inner_abs = abs(f1 + f2)
        outer_abs = abs(inner_abs * f3 - f4)
        
        res = outer_abs * random.randint(2, 5)
        
        expr = f"{random.randint(2, 5)} \\times \\left| \\left| {to_latex(f1)} + {to_latex(f2)} \\right| \\times {to_latex(f3)} - {to_latex(f4)} \\right|"

    if res.denominator == 1:
        ans_str = str(res.numerator)
    else:
        ans_str = f"{res.numerator}/{res.denominator}"

    return {
        'question_text': f"計算 $$   {expr}   $$ 的值。",
        'answer': '',
        'correct_answer': ans_str,
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        ua_str = str(user_answer).strip().replace(' ', '')
        ca_str = str(correct_answer).strip().replace(' ', '')
        
        if ua_str == ca_str:
            return {'correct': True, 'result': '正確'}
        
        if '/' in ua_str:
            ua_parts = ua_str.split('/')
            ua_val = Fraction(int(ua_parts[0]), int(ua_parts[1]))
        else:
            ua_val = Fraction(ua_str)
            
        if '/' in ca_str:
            ca_parts = ca_str.split('/')
            ca_val = Fraction(int(ca_parts[0]), int(ca_parts[1]))
        else:
            ca_val = Fraction(ca_str)
            
        if ua_val == ca_val:
            return {'correct': True, 'result': '正確'}
        return {'correct': False, 'result': '錯誤'}
    except:
        return {'correct': False, 'result': '錯誤'}