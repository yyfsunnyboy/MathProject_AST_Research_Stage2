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

        part1_val = (a + b) * f1
        part1_str = f"\\left[({a} + {b}) \\times {to_latex(f1)}\\right]"
        
        part2_val = f2
        part2_str = f"\\left({to_latex(f2)}\\right)"
        
        part3_val = abs(c * f3 - d)
        part3_str = f"\\left|{c} \\times {to_latex(f3)} - {d}\\right|"
        
        question_text = f"計算 $$   {part1_str} \\div {part2_str} + {part3_str}   $$ 的值。"
        result = (part1_val / part2_val) + part3_val

    elif level == 2:
        nest_str, nest_val = get_nested_latex(1)
        f_extra = get_frac()
        while f_extra == 0:
            f_extra = get_frac()
            
        abs_val = abs(get_frac() - get_frac())
        abs_str = f"\\left|{to_latex(get_frac())} - {to_latex(get_frac())}\\right|"
        # Re-calculate to match string
        f_a = get_frac()
        f_b = get_frac()
        abs_val = abs(f_a - f_b)
        abs_str = f"\\left|{to_latex(f_a)} - {to_latex(f_b)}\\right|"

        question_text = f"計算 $$   {nest_str} \\times \\left({to_latex(f_extra)}\\right)^{-1} - {abs_str}   $$ 的值。"
        result = nest_val * (1/f_extra) - abs_val

    else:
        f1 = get_frac()
        f2 = get_frac()
        f3 = get_frac()
        while f3 == 0: f3 = get_frac()
        
        inner_abs_val = abs(f1 + f2)
        inner_abs_str = f"\\left|{to_latex(f1)} + {to_latex(f2)}\\right|"
        
        outer_val = abs(inner_abs_val * f3 - random.randint(1, 5))
        outer_str = f"\\left|{inner_abs_str} \\times {to_latex(f3)} - {random.randint(1, 5)}\\right|"
        
        # Re-sync random int
        rand_int = random.randint(1, 5)
        outer_val = abs(inner_abs_val * f3 - rand_int)
        outer_str = f"\\left|{inner_abs_str} \\times {to_latex(f3)} - {rand_int}\\right|"
        
        nest_str, nest_val = get_nested_latex(1)
        
        question_text = f"計算 $$   {outer_str} \\div \\left({nest_str}\\right)   $$ 的值。"
        if nest_val == 0:
            nest_val = Fraction(1, 1)
            question_text = f"計算 $$   {outer_str} + \\left({nest_str}\\right)   $$ 的值。"
            result = outer_val + nest_val
        else:
            result = outer_val / nest_val

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