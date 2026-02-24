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
    
    c = random.randint(int_range[0], int_range[1])
    f3 = get_signed_frac()
    d = random.randint(1, 10)

    if level == 2:
        f_top = get_frac()
        f_bot = get_frac()
        f_nested = f_top / f_bot
        nested_latex = f"\\frac{{{to_latex(f_top)}}}{{{to_latex(f_bot)}}}"
        
        part1_val = (a + b) * f1
        part1_str = f"\\left[({a} + {fmt_num(b)}) \\times {to_latex(f1)}\\right]"
        
        part2_val = f_nested
        part2_str = nested_latex
        
        part3_val = abs(c * f3 - d)
        part3_str = f"\\left|{c} \\times {to_latex(f3)} - {d}\\right|"
        
    elif level == 3:
        f_top = get_signed_frac()
        f_bot = get_signed_frac()
        f_nested = f_top / f_bot
        nested_latex = f"\\frac{{{to_latex(f_top)}}}{{{to_latex(f_bot)}}}"
        
        part1_val = abs(a - b) * f1
        part1_str = f"\\left|{a} - {fmt_num(b)}\\right| \\times {to_latex(f1)}"
        
        part2_val = f_nested
        part2_str = f"\\left({nested_latex}\\right)"
        
        inner_val = c + f3
        part3_val = abs(abs(inner_val) - d)
        part3_str = f"\\left| \\left| {c} + {to_latex(f3)} \\right| - {d} \\right|"
    else:
        part1_val = (a + b) * f1
        part1_str = f"\\left[({a} + {fmt_num(b)}) \\times {to_latex(f1)}\\right]"
        
        part2_val = f2
        part2_str = f"\\left({to_latex(f2)}\\right)"
        
        part3_val = abs(c * f3 - d)
        part3_str = f"\\left|{c} \\times {to_latex(f3)} - {d}\\right|"

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
        ua_str = str(user_answer).strip().replace(' ', '')
        ca_str = str(correct_answer).strip().replace(' ', '')
        
        if ua_str == ca_str:
            return {'correct': True, 'result': '正確'}
            
        ua_frac = Fraction(ua_str)
        ca_frac = Fraction(ca_str)
        
        if ua_frac == ca_frac:
            return {'correct': True, 'result': '正確'}
        else:
            return {'correct': False, 'result': '錯誤'}
    except:
        return {'correct': False, 'result': '錯誤'}