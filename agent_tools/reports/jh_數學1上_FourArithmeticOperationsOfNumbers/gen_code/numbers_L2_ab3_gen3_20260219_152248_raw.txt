import random
from fractions import Fraction

def generate(level=1, **kwargs):
    if level == 1:
        int_range = (-10, 10)
        frac_range = (2, 8)
        nest_depth = 0
    elif level == 2:
        int_range = (-20, 20)
        frac_range = (2, 12)
        nest_depth = 1
    else:
        int_range = (-50, 50)
        frac_range = (2, 20)
        nest_depth = 2

    def get_frac():
        d = random.randint(frac_range[0], frac_range[1])
        n = random.randint(1, d * 2)
        if random.choice([True, False]):
            n = -n
        return Fraction(n, d)

    def get_nested_latex(depth):
        if depth <= 0:
            f = get_frac()
            return to_latex(f), f
        
        f1_str, f1_val = get_nested_latex(depth - 1)
        f2_str, f2_val = get_nested_latex(depth - 1)
        op = random.choice(['+', '-'])
        
        if op == '+':
            res_val = f1_val + f2_val
        else:
            res_val = f1_val - f2_val
            
        if res_val == 0:
            res_val = Fraction(1, 1)
            
        num_str, num_val = get_nested_latex(depth - 1)
        
        new_str = f"\\frac{{{num_str}}}{{{f1_str} {op} {f2_str}}}"
        new_val = num_val / res_val
        return new_str, new_val

    if level == 1:
        a = random.randint(int_range[0], int_range[1])
        b = random.randint(1, 10)
        f1 = get_frac()
        f2 = get_frac()
        while f2 == 0:
            f2 = get_frac()
        
        c = random.randint(int_range[0], int_range[1])
        f3 = get_frac()
        d = random.randint(1, 10)

        part1_str = f"\\left[({a} + {b}) \\times {to_latex(f1)}\\right]"
        part2_str = f"\\div {fmt_num(f2)}"
        part3_str = f" + \\left|{c} \\times {to_latex(f3)} - {d}\\right|"
        
        question_text = f"計算 $$   {part1_str} {part2_str} {part3_str}   $$ 的值。"
        
        val1 = (a + b) * f1
        val2 = f2
        val3 = abs(c * f3 - d)
        result = (val1 / val2) + val3

    elif level == 2:
        nest_str, nest_val = get_nested_latex(1)
        f1 = get_frac()
        a = random.randint(1, 10)
        
        part1_str = f"{nest_str} \\times {fmt_num(f1)}"
        part2_str = f" - \\left|{a} \\div {to_latex(get_frac())}\\right|"
        
        question_text = f"計算 $$   {part1_str} {part2_str}   $$ 的值。"
        
        f_abs = get_frac()
        while f_abs == 0: f_abs = get_frac()
        val1 = nest_val * f1
        val2 = abs(a / f_abs)
        result = val1 - val2

    else:
        nest_str, nest_val = get_nested_latex(1)
        f1 = get_frac()
        while f1 == 0: f1 = get_frac()
        
        inner_abs_val = get_frac() - get_frac()
        inner_abs_str = f"\\left|{to_latex(get_frac())} - {to_latex(get_frac())}\\right|"
        
        part1_str = f"\\left| {nest_str} \\div {fmt_num(f1)} - {inner_abs_str} \\right|"
        
        question_text = f"計算 $$   {part1_str}   $$ 的值。"
        
        f_div = f1
        val_inner = abs(get_frac() - get_frac())
        result = abs((nest_val / f_div) - val_inner)

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