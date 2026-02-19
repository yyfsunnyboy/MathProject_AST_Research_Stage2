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

    a = random.randint(int_range[0], int_range[1])
    b = random.randint(1, max(5, int_range[1]))
    f1 = get_frac()
    
    part1_val = (a + b) * f1
    part1_str = f"\\left[({a} + {b}) \\times {to_latex(f1)}\\right]"

    f2 = get_signed_frac()
    while f2 == 0:
        f2 = get_signed_frac()
    
    part2_str = f"\\div \\left({to_latex(f2)}\\right)"
    
    c = random.randint(int_range[0], int_range[1])
    f3 = get_signed_frac()
    d = random.randint(1, max(5, int_range[1]))
    
    part3_val = abs(c * f3 - d)
    part3_str = f"+ \\left|{c} \\times {to_latex(f3)} - {d}\\right|"

    if level == 2:
        nf_n = get_frac()
        nf_d = get_frac()
        nf = nf_n / nf_d
        part1_str = f"\\left[\\frac{{{to_latex(nf_n)}}}{{{to_latex(nf_d)}}} + {a}\\right]"
        part1_val = nf + a
    
    if level == 3:
        inner_abs_val = abs(get_signed_frac() - random.randint(1, 5))
        part3_val = abs(c * f3 - inner_abs_val)
        part3_str = f"+ \\left|{c} \\times {to_latex(f3)} - \\left|{to_latex(get_signed_frac() - Fraction(d, 1))}\\right| \\right|"

    question_text = f"計算 $$   {part1_str} {part2_str} {part3_str}   $$ 的值。"
    
    final_result = (part1_val / f2) + part3_val
    
    if final_result.denominator == 1:
        correct_answer = str(final_result.numerator)
    else:
        correct_answer = f"{final_result.numerator}/{final_result.denominator}"

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
        
        if "/" in ua_str:
            ua_parts = ua_str.split('/')
            ua = Fraction(int(ua_parts[0]), int(ua_parts[1]))
        else:
            ua = Fraction(ua_str)
            
        if "/" in ca_str:
            ca_parts = ca_str.split('/')
            ca = Fraction(int(ca_parts[0]), int(ca_parts[1]))
        else:
            ca = Fraction(ca_str)
            
        if ua == ca:
            return {'correct': True, 'result': '正確'}
        else:
            return {'correct': False, 'result': '錯誤'}
    except:
        return {'correct': False, 'result': '錯誤'}