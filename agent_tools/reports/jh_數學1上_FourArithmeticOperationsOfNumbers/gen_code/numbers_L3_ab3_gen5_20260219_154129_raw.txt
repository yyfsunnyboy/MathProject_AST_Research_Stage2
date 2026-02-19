import random
from fractions import Fraction

def generate(level=1, **kwargs):
    if level == 1:
        int_range = (-10, 10)
        frac_range = (1, 8)
    elif level == 2:
        int_range = (-20, 20)
        frac_range = (1, 12)
    else:
        int_range = (-50, 50)
        frac_range = (1, 20)

    def get_frac():
        n = random.randint(1, frac_range[1])
        d = random.randint(2, frac_range[1])
        return Fraction(n, d)

    def get_signed_frac():
        n = random.choice([-1, 1]) * random.randint(1, frac_range[1])
        d = random.randint(2, frac_range[1])
        return Fraction(n, d)

    a = random.randint(*int_range)
    b = random.randint(1, 10)
    f1 = get_frac()
    
    part1_val = (a + b) * f1
    part1_str = f"\\left[({a} + {b}) \\times {to_latex(f1)}\\right]"

    f2 = get_signed_frac()
    while f2 == 0:
        f2 = get_signed_frac()
    
    part2_str = f"\\div \\left({to_latex(f2)}\\right)" if f2 < 0 else f"\\div {to_latex(f2)}"
    
    c = random.randint(*int_range)
    f3 = get_signed_frac()
    d = random.randint(1, 10)
    
    abs_inner_val = (c * f3) - d
    part3_val = abs(abs_inner_val)
    part3_str = f"+ \\left|{c} \\times {to_latex(f3)} - {d}\\right|"

    if level == 2:
        f4 = get_frac()
        f5 = get_frac()
        nested_frac = f4 / f5
        part1_str = f"\\left[\\frac{{{to_latex(f4)}}}{{{to_latex(f5)}}} + {a}\\right]"
        part1_val = nested_frac + a
    
    if level == 3:
        f6 = get_signed_frac()
        part3_val = abs(abs(c * f3) - abs(d * f6))
        part3_str = f"+ \\left| \\left| {c} \\times {to_latex(f3)} \\right| - \\left| {d} \\times {to_latex(f6)} \\right| \\right|"

    result = (part1_val / f2) + part3_val
    
    question_text = f"計算 $$   {part1_str} {part2_str} {part3_str}   $$ 的值。"
    
    if result.denominator == 1:
        correct_answer = str(result.numerator)
    else:
        correct_answer = f"{result.numerator}/{result.denominator}"
        
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
        
        ua = float(Fraction(ua_str))
        ca = float(Fraction(ca_str))
        
        if abs(ua - ca) < 1e-9:
            return {'correct': True, 'result': '正確'}
            
        return {'correct': False, 'result': '錯誤'}
    except:
        return {'correct': False, 'result': '錯誤'}