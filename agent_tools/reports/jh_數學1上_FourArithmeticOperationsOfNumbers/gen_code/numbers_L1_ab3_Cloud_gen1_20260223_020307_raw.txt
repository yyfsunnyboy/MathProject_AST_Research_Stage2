import random
from fractions import Fraction

def generate(level=1, **kwargs):
    if level == 1:
        int_range = (-10, 10)
        frac_range = (2, 8)
    elif level == 2:
        int_range = (-20, 20)
        frac_range = (2, 12)
    else:
        int_range = (-50, 50)
        frac_range = (2, 20)

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
    if a + b == 0: a += 1
    
    f1 = get_frac()
    f2 = get_signed_frac()
    if f2 == 0: f2 = Fraction(1, 2)
    
    f3 = get_signed_frac()
    c = random.randint(int_range[0], int_range[1])
    d = random.randint(1, 10)

    if level == 1:
        part1_val = (a + b) * f1
        part1_str = f"\\left[({a} + {fmt_num(b)}) \\times {to_latex(f1)}\\right]"
        
        part2_val = f2
        part2_str = f"{to_latex(f2)}"
        if f2 < 0:
            part2_str = f"\\left({part2_str}\\right)"
            
        part3_val = abs(c * f3 - d)
        part3_str = f"\\left|{c} \\times {to_latex(f3)} - {d}\\right|"
        
        question_text = f"計算 $$   {part1_str} \\div {part2_str} + {part3_str}   $$ 的值。"
        result = (part1_val / part2_val) + part3_val

    elif level == 2:
        top_n = random.randint(1, 5)
        top_d = get_frac()
        bot_n = get_frac()
        bot_d = random.randint(1, 5)
        
        f_nested = Fraction(top_n, top_d) / Fraction(bot_n, bot_d)
        nested_latex = f"\\frac{{\\frac{{{top_n}}}{{{to_latex(top_d)}}}}}{{\\frac{{{to_latex(bot_n)}}}{{{bot_d}}}}}"
        
        part1_val = f_nested + a
        part1_str = f"\\left({nested_latex} + {fmt_num(a)}\\right)"
        
        f_div = get_signed_frac()
        part2_val = f_div
        part2_str = f"{to_latex(f_div)}"
        if f_div < 0:
            part2_str = f"\\left({part2_str}\\right)"
            
        part3_val = abs(f3 * b)
        part3_str = f"\\left|{to_latex(f3)} \\times {fmt_num(b)}\\right|"
        
        question_text = f"計算 $$   {part1_str} \\div {part2_str} - {part3_str}   $$ 的值。"
        result = (part1_val / part2_val) - part3_val

    else:
        f_inner = get_signed_frac()
        inner_abs_val = abs(f_inner * a - b)
        inner_abs_str = f"\\left|{to_latex(f_inner)} \\times {fmt_num(a)} - {fmt_num(b)}\\right|"
        
        part1_val = abs(inner_abs_val - d)
        part1_str = f"\\left| {inner_abs_str} - {d} \\right|"
        
        f_mul = get_signed_frac()
        part2_val = f_mul
        part2_str = f"{to_latex(f_mul)}"
        if f_mul < 0:
            part2_str = f"\\left({part2_str}\\right)"
            
        f_add = get_signed_frac()
        part3_val = f_add
        part3_str = f"{to_latex(f_add)}"
        
        question_text = f"計算 $$   {part1_str} \\times {part2_str} + {part3_str}   $$ 的值。"
        result = (part1_val * part2_val) + part3_val

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