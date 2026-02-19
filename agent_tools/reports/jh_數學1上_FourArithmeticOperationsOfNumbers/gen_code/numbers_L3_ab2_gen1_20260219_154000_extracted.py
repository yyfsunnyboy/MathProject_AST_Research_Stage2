import random
from fractions import Fraction

def generate(level=1, **kwargs):
    if level == 1:
        int_range = (-10, 10)
        frac_range = (1, 8)
    elif level == 2:
        int_range = (-20, 20)
        frac_range = (1, 15)
    else:
        int_range = (-50, 50)
        frac_range = (1, 25)

    def get_frac():
        n = random.randint(1, frac_range[1])
        d = random.randint(2, frac_range[1])
        return Fraction(n, d)

    def get_signed_frac():
        n = random.choice([-1, 1]) * random.randint(1, frac_range[1])
        d = random.randint(2, frac_range[1])
        return Fraction(n, d)

    if level == 1:
        a = random.randint(int_range[0], int_range[1])
        b = random.randint(1, 10)
        f1 = get_frac()
        f2 = get_signed_frac()
        f3 = get_signed_frac()
        c = random.randint(1, 10)
        
        part1_val = (a + b) * f1
        part1_str = f"\\left[({a} + {b}) \\times {to_latex(f1)}\\right]"
        
        part2_val = f2
        part2_str = f"\\left({to_latex(f2)}\\right)"
        
        part3_val = abs(c * f3 - random.randint(1, 5))
        part3_str = f"\\left|{c} \\times {to_latex(f3)} - {random.randint(1, 5)}\\right|"
        
        res = (part1_val / part2_val) + part3_val
        question_text = f"計算 $$   {part1_str} \\div {part2_str} + {part3_str}   $$ 的值。"

    elif level == 2:
        f1 = get_frac()
        f2 = get_frac()
        f3 = get_frac()
        f4 = get_frac()
        
        nested_top = f1 + f2
        nested_bottom = f3 - f4
        if nested_bottom == 0: nested_bottom = Fraction(1, 1)
        
        nested_val = nested_top / nested_bottom
        nested_str = f"\\frac{{{to_latex(f1)} + {to_latex(f2)}}}{{{to_latex(f3)} - {to_latex(f4)}}}"
        
        f5 = get_signed_frac()
        part2_str = f"\\left({to_latex(f5)}\\right)"
        
        res = nested_val * f5
        question_text = f"計算 $$   {nested_str} \\times {part2_str}   $$ 的值。"

    else:
        f1 = get_signed_frac()
        f2 = get_signed_frac()
        f3 = get_signed_frac()
        f4 = get_signed_frac()
        
        inner_abs_val = abs(f1 * f2 - f3)
        inner_abs_str = f"\\left|{to_latex(f1)} \\times {to_latex(f2)} - {to_latex(f3)}\\right|"
        
        outer_abs_val = abs(inner_abs_val / f4 if f4 != 0 else inner_abs_val)
        outer_abs_str = f"\\left|{inner_abs_str} \\div {to_latex(f4)}\\right|"
        
        res = outer_abs_val
        question_text = f"計算 $$   {outer_abs_str}   $$ 的值。"

    if res.denominator == 1:
        correct_answer = str(res.numerator)
    else:
        correct_answer = f"{res.numerator}/{res.denominator}"

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