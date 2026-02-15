# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfNumbers
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 322.55s | Tokens: In=635, Out=7338
# Created At: 2026-02-15 15:21:03
# Fix Status: [No Healer - Bare LLM Output] | Fixes: Basic=0, Advanced=None
# Verification: Internal Logic Check = PASSED
# ==============================================================================

import random
from fractions import Fraction

def generate(level=1, **kwargs):
    def generate_fraction():
        numerator = random.randint(-10, 10)
        denominator = random.randint(1, 10)
        return Fraction(numerator, denominator)
    
    a = generate_fraction()
    b = generate_fraction()
    c = generate_fraction()
    d = generate_fraction()
    e = generate_fraction()
    f = generate_fraction()
    g = generate_fraction()
    h = generate_fraction()
    i = generate_fraction()
    
    a_text = f"{a.numerator}/{a.denominator}" if a.denominator != 1 else f"{a.numerator}"
    b_text = f"{b.numerator}/{b.denominator}" if b.denominator != 1 else f"{b.numerator}"
    c_text = f"{c.numerator}/{c.denominator}" if c.denominator != 1 else f"{c.numerator}"
    d_text = f"{d.numerator}/{d.denominator}" if d.denominator != 1 else f"{d.numerator}"
    e_text = f"{e.numerator}/{e.denominator}" if e.denominator != 1 else f"{e.numerator}"
    f_text = f"{f.numerator}/{f.denominator}" if f.denominator != 1 else f"{f.numerator}"
    g_text = f"{g.numerator}/{g.denominator}" if g.denominator != 1 else f"{g.numerator}"
    h_text = f"{h.numerator}/{h.denominator}" if h.denominator != 1 else f"{h.numerator}"
    i_text = f"{i.numerator}/{i.denominator}" if i.denominator != 1 else f"{i.numerator}"
    
    bracket_part = f"(-{a_text} + {b_text}) × {c_text}/{d_text}"
    division_part = f"÷ (-{e_text}/{f_text})"
    absolute_part = f"|{g_text} × {h_text} - {i_text}|"
    question_text = f"[{bracket_part}]{division_part} + {absolute_part}"
    
    a_str = f"Fraction({a.numerator}, {a.denominator})"
    b_str = f"Fraction({b.numerator}, {b.denominator})"
    c_str = f"Fraction({c.numerator}, {c.denominator})"
    d_str = f"Fraction({d.numerator}, {d.denominator})"
    e_str = f"Fraction({e.numerator}, {e.denominator})"
    f_str = f"Fraction({f.numerator}, {f.denominator})"
    g_str = f"Fraction({g.numerator}, {g.denominator})"
    h_str = f"Fraction({h.numerator}, {h.denominator})"
    i_str = f"Fraction({i.numerator}, {i.denominator})"
    
    expr_str = f"((-{a_str} + {b_str}) * ({c_str}/{d_str})) / (-{e_str}/{f_str}) + abs({g_str} * {h_str} - {i_str})"
    
    try:
        correct_answer = eval(expr_str)
    except ZeroDivisionError:
        return generate(level=level)
    
    if correct_answer.denominator == 1:
        correct_answer_str = f"{correct_answer.numerator}"
    else:
        correct_answer_str = f"{correct_answer.numerator}/{correct_answer.denominator}"
    
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer_str,
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        user_fraction = Fraction(user_answer)
        correct_fraction = Fraction(correct_answer)
        return {
            'correct': user_fraction == correct_fraction,
            'result': '正確' if user_fraction == correct_fraction else '錯誤'
        }
    except:
        return {
            'correct': False,
            'result': '錯誤'
        }