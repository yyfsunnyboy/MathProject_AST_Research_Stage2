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
        f2 = f_top / f_bot
        f2_latex = f"\\frac{{{to_latex(f_top)}}}{{{to_latex(f_bot)}}}"
    else:
        f2_latex = to_latex(f2)

    if f2 < 0:
        f2_str = f"\\left({f2_latex}\\right)"
    else:
        f2_str = f2_latex

    part1_val = (a + b) * f1
    part1_str = f"\\left[({a} + {fmt_num(b)}) \\times {to_latex(f1)}\\right]"
    
    part3_val = abs(c * f3 - d)
    part3_str = f"\\left|{c} \\times {to_latex(f3)} - {d}\\right|"

    question_text = f"計算 $$   {part1_str} \\div {f2_str} + {part3_str}   $$ 的值。"
    
    result = (part1_val / f2) + part3_val
    
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
        
        if '/' in ua_str:
            ua_parts = ua_str.split('/')
            if len(ua_parts) == 2:
                ua_val = Fraction(int(ua_parts[0]), int(ua_parts[1]))
            else:
                return {'correct': False, 'result': '錯誤'}
        else:
            ua_val = Fraction(ua_str)
            
        ca_val = Fraction(ca_str)
        
        if ua_val == ca_val:
            return {'correct': True, 'result': '正確'}
        else:
            return {'correct': False, 'result': '錯誤'}
    except:
        return {'correct': False, 'result': '錯誤'}