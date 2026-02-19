import random
from fractions import Fraction

def generate(level=1, **kwargs):
    if level == 1:
        int_range = (-5, 5)
        frac_range = (2, 6)
        abs_range = (1, 5)
    elif level == 2:
        int_range = (-10, 10)
        frac_range = (2, 10)
        abs_range = (5, 15)
    else:
        int_range = (-20, 20)
        frac_range = (2, 15)
        abs_range = (10, 30)

    def get_frac():
        d = random.randint(frac_range[0], frac_range[1])
        n = random.randint(1, d * 2)
        if n % d == 0:
            n += 1
        return Fraction(n, d)

    def get_signed_frac():
        f = get_frac()
        return f * random.choice([-1, 1])

    a = random.randint(int_range[0], int_range[1])
    b = random.randint(int_range[0], int_range[1])
    if a + b == 0: b += 1
    
    f1 = get_frac()
    f2 = get_signed_frac()
    
    f3 = get_signed_frac()
    c = random.randint(int_range[0], int_range[1])
    if c == 0: c = 1
    d = random.randint(abs_range[0], abs_range[1])

    part1_val = (a + b) * f1
    part1_str = f"\\left[({a} + {fmt_num(b)}) \\times {to_latex(f1)}\\right]"
    
    part2_val = f2
    part2_str = f"\\left({to_latex(f2)}\\right)"
    
    part3_inner_val = c * f3 - d
    part3_val = abs(part3_inner_val)
    part3_str = f"\\left|{c} \\times {to_latex(f3)} - {d}\\right|"

    if level == 2:
        nf_n = get_frac()
        nf_d = get_frac()
        nf_val = nf_n / nf_d
        nf_str = f"\\frac{{{to_latex(nf_n)}}}{{{to_latex(nf_d)}}}"
        
        question_text = f"計算 $$   {part1_str} \\div {part2_str} + {nf_str} - {part3_str}   $$ 的值。"
        result = (part1_val / part2_val) + nf_val - part3_val
    elif level == 3:
        f4 = get_signed_frac()
        inner_abs_val = abs(a * f4 - b)
        inner_abs_str = f"\\left|{a} \\times {to_latex(f4)} - {b}\\right|"
        
        outer_abs_val = abs(part1_val / part2_val - inner_abs_val)
        question_text = f"計算 $$   \\left| {part1_str} \\div {part2_str} - {inner_abs_str} \\right| + {to_latex(f3)}   $$ 的值。"
        result = outer_abs_val + f3
    else:
        question_text = f"計算 $$   {part1_str} \\div {part2_str} + {part3_str}   $$ 的值。"
        result = (part1_val / part2_val) + part3_val

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