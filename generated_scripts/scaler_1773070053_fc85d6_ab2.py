import random
import math
from fractions import Fraction


def generate(level=1, **kwargs):
    for _ in range(100):
        try:
            # Step 1: 生成分子/分母（分母2-10正整数，分子可正可负）
            n1 = IntegerOps.random_nonzero(-99, 99)
            d1 = IntegerOps.random_nonzero(2, 10)
            n2 = IntegerOps.random_nonzero(-99, 99)
            d2 = IntegerOps.random_nonzero(2, 10)

            # Step 2: 预计算答案（Fraction精确计算）
            eval_str = f"Fraction({n1}, {d1}) * Fraction({n2}, {d2})"
            ans = safe_eval(eval_str)

            # Step 3: D6 单一过滤（阈值120，无运算符优先级陷阱）
            if not isinstance(ans, Fraction) or abs(ans.numerator) > 120 or ans.denominator > 120:
                continue

            # Step 4: 组装带分数显示字串（关键：mixed=True强制带分数格式）
            f1_str = FractionOps.to_latex(Fraction(n1, d1), mixed=True)
            f2_str = FractionOps.to_latex(Fraction(n2, d2), mixed=True)
            math_str = f"({f1_str}) \\times ({f2_str})"

            # Step 5: 美观检核
            if "}{1}" in math_str:
                continue

            # Step 6: 格式化答案（分母为1时显示整数）
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