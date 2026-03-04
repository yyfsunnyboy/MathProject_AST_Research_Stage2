import random
import math
from fractions import Fraction


def generate(level=1, **kwargs):
    for _ in range(30):
        _o1_healed = False
        try:
            # 1) 依原始常數位置產生變數（含分子/分母）
            n1 = IntegerOps.random_nonzero(-50, 50)
            d1 = IntegerOps.random_nonzero(-10, 10)
            n2 = IntegerOps.random_nonzero(-50, 50)
            d2 = IntegerOps.random_nonzero(-10, 10)
            n3 = IntegerOps.random_nonzero(-50, 50)
            d3 = IntegerOps.random_nonzero(-10, 10)

            # 2) 預先測試算式，使用 Fraction(...) 保留精確分母
            eval_str_init = f"Fraction({n1},{d1}) - Fraction({n2},{d2}) + Fraction({n3},{d3})"
            ans_init = safe_eval(eval_str_init)

            # 3) O(1) 攔截：分母異常放大時直接換樣本
            if isinstance(ans_init, Fraction) and ans_init.denominator > 120:
                continue

            # 4) 七年級友善範圍過濾（不做強制整數化）
            if isinstance(ans_init, Fraction):
                if abs(ans_init.numerator) > 120 or ans_init.denominator > 36:
                    continue
                _o1_healed = False

            # 5) 重新組裝正式字串
            eval_str = f"Fraction({n1},{d1}) - Fraction({n2},{d2}) + Fraction({n3},{d3})"
            math_str = f"\\frac{{{n1}}}{{{d1}}} - \\frac{{{n2}}}{{{d2}}} + \\frac{{{n3}}}{{{d3}}}"

            # 5.1) 題面美觀檢核（必要）
            if "}{1}" in math_str:
                continue

            # 5.2) 分子硬限制（必要）
            if max(abs(n1), abs(n2), abs(n3)) > 99:
                continue

            ans = safe_eval(eval_str)
            if isinstance(ans, Fraction):
                if abs(ans.numerator) > 40 or ans.denominator > 12:
                    continue
                if ans.denominator == 1:
                    correct_answer = str(ans.numerator)
                else:
                    correct_answer = f"{ans.numerator}/{ans.denominator}"
            else:
                f_ans = Fraction(ans).limit_denominator()
                if f_ans.denominator == 1:
                    correct_answer = str(f_ans.numerator)
                else:
                    correct_answer = f"{f_ans.numerator}/{f_ans.denominator}"

            return {
                'question_text': '計算 $' + math_str + '$ 的值。',
                'answer': '',
                'correct_answer': correct_answer,
                'mode': 1,
                '_o1_healed': _o1_healed
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