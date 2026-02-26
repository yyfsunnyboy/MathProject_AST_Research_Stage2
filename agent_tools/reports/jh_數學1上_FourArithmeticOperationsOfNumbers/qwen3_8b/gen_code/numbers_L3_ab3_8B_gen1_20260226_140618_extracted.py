import random
from fractions import Fraction

def generate(level=1, **kwargs):
    if level == 1:
        int_range = (-5, 5)
        frac_range = (1, 6)
    elif level == 2:
        int_range = (-20, 20)
        frac_range = (1, 12)
    else:  # level 3
        int_range = (-100, 100)
        frac_range = (1, 20)
    
    # Part 1: Bracket with fractions
    a = random.randint(*int_range)
    b = random.randint(1, int_range[1])
    num1 = random.randint(1, frac_range[1])
    den1 = random.randint(2, frac_range[1])
    frac1 = Fraction(num1, den1)
    
    part1_str = f"\\left[({a}+{b}) \\times {to_latex(frac1)}\\right]"
    
    # Part 2: Division by fraction
    num2 = random.randint(-frac_range[1], -1)
    den2 = random.randint(2, frac_range[1])
    frac2 = Fraction(num2, den2)
    part2_str = f"\\left({to_latex(frac2)}\\right)"
    
    # Part 3: Absolute value with fraction
    c = random.randint(int_range[0]//2, int_range[1]//2)
    num3 = random.randint(-frac_range[1], -1)
    den3 = random.randint(2, frac_range[1])
    frac3 = Fraction(num3, den3)
    d = random.randint(1, frac_range[1])
    
    part3_str = f"\\left|{c} \\times {to_latex(frac3)} - {d}\\right|"
    
    question_text = f"計算 $$ {part1_str} \\div {part2_str} + {part3_str} $$ 的值。"
    
    val1 = (a + b) * frac1
    val2 = frac2
    val3 = abs((c * frac3) - d)
    
    result = (val1 / val2) + val3
    
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