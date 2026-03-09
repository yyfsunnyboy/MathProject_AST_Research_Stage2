import random
import math
from fractions import Fraction


def generate(level=1, **kwargs):
    for _ in range(100):
        try:
            # Step 1: 生成带分数结构（-a b/c 和 d e/f）
            n1 = IntegerOps.random_nonzero(-99, 99)
            d1 = IntegerOps.random_nonzero(2, 10)
            n2 = IntegerOps.random_nonzero(-99, 99)
            d2 = IntegerOps.random_nonzero(2, 10)

            # Step 2: 构造带分数表达式
            expr = f"Fraction({n1}, {d1}) + Fraction({n2}, {d2})"
            ans = safe_eval(expr)

            # Step 3: 过滤条件（阈值 120）
            if not isinstance(ans, Fraction) or abs(ans.numerator) > 120 or ans.denominator > 120:
                continue

            # Step 4: 转换为带分数显示格式
            f1_str = FractionOps.to_latex(Fraction(n1, d1), mixed=True)
            f2_str = FractionOps.to_latex(Fraction(n2, d2), mixed=True)
            math_str = f"({f1_str}) + ({f2_str})"

            # Step 5: 美观检查
            if "}{1}" in math_str:
                continue

            # Step 6: 格式化答案
            if ans.denominator == 1:
                correct_answer = str(ans.numerator)
            else:
                correct_answer = f"{ans.numerator}/{ans.denominator}"

            return {
                'question_text': '計算 $' + math_str + '$ 的值。',
                'answer': '',
                'correct_answer': correct_answer,
                'mode': 1,
                '_o1_healed': False
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