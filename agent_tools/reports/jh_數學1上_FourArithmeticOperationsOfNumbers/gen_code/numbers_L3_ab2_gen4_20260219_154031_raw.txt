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
    if a + b == 0: b += 1
    
    f1 = get_signed_frac()
    f2 = get_signed_frac()
    if f2 == 0: f2 = Fraction(1, 2)
    
    f3 = get_signed_frac()
    c = random.randint(int_range[0], int_range[1])
    d = random.randint(1, 10)

    if level == 1:
        part1_val = (a + b) * f1
        part1_str = f"\\left[({a} + {fmt_num(b)}) \\times {to_latex(f1)}\\right]"
        
        part2_val = f2
        part2_str = to_latex(f2)
        
        part3_val = abs(c * f3 - d)
        part3_str = f"\\left|{c} \\times {to_latex(f3)} - {d}\\right|"
        
        op = random.choice(['+', '-'])
        question_text = f"計算 $$   {part1_str} \\div {part2_str} {op} {part3_str}   $$ 的值。"
        
        if op == '+':
            res = (part1_val / part2_val) + part3_val
        else:
            res = (part1_val / part2_val) - part3_val

    elif level == 2:
        top_n = get_signed_frac()
        bot_n = get_signed_frac()
        if bot_n == 0: bot_n = Fraction(1, 3)
        nested_f = top_n / bot_n
        
        part1_str = f"\\frac{{{to_latex(top_n)}}}{{{to_latex(bot_n)}}}"
        part2_val = get_signed_frac()
        part2_str = to_latex(part2_val)
        
        part3_val = abs(f1 + f2 * f3)
        part3_str = f"\\left|{to_latex(f1)} + {to_latex(f2)} \\times {to_latex(f3)}\\right|"
        
        question_text = f"計算 $$   {part1_str} \\div {part2_str} - {part3_str}   $$ 的值。"
        res = (nested_f / part2_val) - part3_val

    else:
        f_inner = get_signed_frac()
        val_inner = abs(f_inner - a)
        part1_str = f"\\left| \\left| {to_latex(f_inner)} \\right| - {a} \\right|"
        
        f_outer = get_signed_frac()
        part2_str = to_latex(f_outer)
        
        part3_val = (f1 - f2) * f3
        part3_str = f"\\left({to_latex(f1)} - {to_latex(f2)}\\right) \\times {to_latex(f3)}"
        
        question_text = f"計算 $$   {part1_str} \\times {part2_str} + {part3_str}   $$ 的值。"
        res = (Fraction(abs(abs(f_inner) - a)) * f_outer) + part3_val

    if res.denominator == 1:
        ans_str = str(res.numerator)
    else:
        ans_str = f"{res.numerator}/{res.denominator}"

    return {
        'question_text': question_text,
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