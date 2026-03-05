import random
import math
from fractions import Fraction


def generate(level=1, **kwargs):
    fmt = IntegerOps.fmt_num

    if level == 1:
        n_min, n_max = -50, 50
        d_min, d_max = -10, 10
    elif level == 2:
        n_min, n_max = -50, 50
        d_min, d_max = -10, 10
    else:
        n_min, n_max = -50, 50
        d_min, d_max = -10, 10

    def rand_frac():
        num = IntegerOps.random_nonzero(n_min, n_max)
        den = random.randint(d_min, d_max)
        while den == 0 or abs(den) == 1:
            den = random.randint(d_min, d_max)
        return Fraction(num, den)

    def latex_frac_clean(x):
        x = Fraction(x)
        if x.denominator == 1:
            return str(x.numerator)
        return FractionOps.to_latex(x)

    for _ in range(40):
        try:
            a = rand_frac()
            b = rand_frac()
            c = rand_frac()
            d = rand_frac()
            e = rand_frac()
            f = rand_frac()
            g = rand_frac()
            h = rand_frac()

            if c == 0 or f == 0:
                continue

            p1_val = (a + b) * c
            p2_val = d
            p3_val = abs(e * f - g)

            p1_str = f"\\left[{latex_frac_clean(a)} + {latex_frac_clean(b)}\\right] \\times {latex_frac_clean(c)}"
            p2_str = f"\\left({latex_frac_clean(p2_val)}\\right)"
            p3_str = f"\\left|{latex_frac_clean(e)} \\times {latex_frac_clean(f)} - {latex_frac_clean(g)}\\right|"

            if level == 1:
                math_str = f"\\left[{p1_str}\\right] \\div {p2_str} + {p3_str}"
                ans = Fraction(p1_val, 1) / p2_val + p3_val
            elif level == 2:
                p4_val = abs(a - b / c)
                p4_str = f"\\left|{latex_frac_clean(a)} - {latex_frac_clean(b)} \\div {latex_frac_clean(c)}\\right|"
                math_str = f"\\left[{p1_str} - {latex_frac_clean(h)}\\right] \\div {p2_str} + {p4_str}"
                ans = (p1_val - h) / p2_val + p4_val
            else:
                p4_val = h
                p4_str = latex_frac_clean(p4_val)
                math_str = f"-\\left[{p1_str}\\right] + {p3_str} - \\left({latex_frac_clean(d)} \\div {latex_frac_clean(f)}\\right) + {p4_str}"
                ans = -p1_val + p3_val - (d / f) + p4_val

            if ans.denominator == 1:
                correct = str(ans.numerator)
            else:
                correct = f"{ans.numerator}/{ans.denominator}"

            if abs(ans.numerator) > 120 or ans.denominator > 30:
                continue

            if any(abs(x.numerator) > 50 for x in [a, b, c, d, e, f, g, h]):
                continue

            return {
                'question_text': f'計算 $' + math_str + '$ 的值。',
                'answer': '',
                'correct_answer': correct,
                'mode': 1
            }
        except Exception:
            continue

    return {'question_text': 'Error', 'answer': '', 'correct_answer': '0', 'mode': 1}


def check(user_answer, correct_answer):
    try:
        ua = str(user_answer).strip()
        ca = str(correct_answer).strip()
        if ua == ca:
            return {'correct': True, 'result': '正確'}
        if Fraction(ua) == Fraction(ca):
            return {'correct': True, 'result': '正確'}
    except Exception:
        pass
    return {'correct': False, 'result': '錯誤'}