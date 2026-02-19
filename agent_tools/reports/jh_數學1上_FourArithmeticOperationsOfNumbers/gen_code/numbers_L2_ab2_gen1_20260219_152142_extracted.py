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
    b = random.randint(1, 10)
    f1 = get_signed_frac()
    f2 = get_signed_frac()
    if f2 == 0: f2 = Fraction(1, 2)
    
    c = random.randint(int_range[0], int_range[1])
    f3 = get_signed_frac()
    d = random.randint(1, 10)

    if level == 1:
        part1_val = (a + b) * f1
        part1_str = f"\\left[({a} + {b}) \\times {to_latex(f1)}\\right]"
        part2_val = f2
        part2_str = f"{to_latex(f2)}"
        part3_val = abs(c * f3 - d)
        part3_str = f"\\left|{c} \\times {to_latex(f3)} - {d}\\right|"
        
        res_val = (part1_val / part2_val) + part3_val
        question_text = f"計算 $$   {part1_str} \\div {part2_str} + {part3_str}   $$ 的值。"

    elif level == 2:
        f4 = get_frac()
        f5 = get_frac()
        nested_frac_val = f4 / f5
        nested_frac_str = f"\\frac{{{to_latex(f4)}}}{{{to_latex(f5)}}}"
        
        part1_val = (a - f1) * nested_frac_val
        part1_str = f"\\left[({a} - {to_latex(f1)}) \\times {nested_frac_str}\\right]"
        
        part3_val = abs(f2 * f3 - b)
        part3_str = f"\\left|{to_latex(f2)} \\times {to_latex(f3)} - {b}\\right|"
        
        res_val = part1_val + part3_val
        question_text = f"計算 $$   {part1_str} + {part3_str}   $$ 的值。"

    else:
        f4 = get_signed_frac()
        f5 = get_signed_frac()
        inner_abs_val = abs(f4 - f5)
        inner_abs_str = f"\\left|{to_latex(f4)} - {to_latex(f5)}\\right|"
        
        part1_val = (a * f1) / f2
        part1_str = f"\\left({a} \\times {to_latex(f1)} \\div {to_latex(f2)}\\right)"
        
        outer_abs_val = abs(part1_val - inner_abs_val)
        outer_abs_str = f"\\left|{part1_str} - {inner_abs_str}\\right|"
        
        res_val = outer_abs_val * Fraction(1, 2)
        question_text = f"計算 $$   {outer_abs_str} \\times \\frac{{1}}{{2}}   $$ 的值。"

    if res_val.denominator == 1:
        correct_answer = str(res_val.numerator)
    else:
        correct_answer = f"{res_val.numerator}/{res_val.denominator}"

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
            ua_parts = ua_str.split("/")
            ua = Fraction(int(ua_parts[0]), int(ua_parts[1]))
        else:
            ua = Fraction(ua_str)
        if "/" in ca_str:
            ca_parts = ca_str.split("/")
            ca = Fraction(int(ca_parts[0]), int(ca_parts[1]))
        else:
            ca = Fraction(ca_str)
        if ua == ca:
            return {'correct': True, 'result': '正確'}
        return {'correct': False, 'result': '錯誤'}
    except:
        return {'correct': False, 'result': '錯誤'}