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
            
        part1_val = (a + b) * f1
        part1_str = f"\\left[({a} + {b}) \\times {to_latex(f1)}\\right]"
        
        part2_val = f2
        part2_str = f"{fmt_num(f2)}"
        
        c = random.randint(int_range[0], int_range[1])
        f3 = get_frac()
        d = random.randint(1, 10)
        
        part3_val = abs(c * f3 - d)
        part3_str = f"\\left|{c} \\times {to_latex(f3)} - {d}\\right|"
        
        question_text = f"計算 $$   {part1_str} \\div {part2_str} + {part3_str}   $$ 的值。"
        result = (part1_val / part2_val) + part3_val

    elif level == 2:
        nest_str, nest_val = get_nested_latex(1)
        f1 = get_frac()
        while f1 == 0:
            f1 = get_frac()
        
        a = random.randint(int_range[0], int_range[1])
        
        part1_str = f"\\left({nest_str} \\div {to_latex(f1)}\\right)"
        part1_val = nest_val / f1
        
        part2_str = f"\\left|{a} - {to_latex(get_frac())}\\right|"
        part2_val = abs(a - get_frac())
        
        question_text = f"計算 $$   {part1_str} - {part2_str}   $$ 的值。"
        result = part1_val - part2_val

    else:
        nest_str, nest_val = get_nested_latex(2)
        f1 = get_frac()
        while f1 == 0:
            f1 = get_frac()
            
        a = random.randint(int_range[0], int_range[1])
        b = random.randint(int_range[0], int_range[1])
        
        inner_val = a * f1 + b
        inner_str = f"{a} \\times {to_latex(f1)} + {fmt_num(b)}"
        
        part1_str = f"\\left| \\left| {inner_str} \\right| - {to_latex(nest_val)} \\right|"
        part1_val = abs(abs(inner_val) - nest_val)
        
        f2 = get_frac()
        while f2 == 0:
            f2 = get_frac()
            
        question_text = f"計算 $$   {part1_str} \\div {to_latex(f2)}   $$ 的值。"
        result = part1_val / f2

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