import random
import math
from fractions import Fraction


def generate(level=1, **kwargs):
    for _ in range(30):
        try:
            # Step D1: 讀取目標題型結構
            # 原題：計算 $(-2又1/6) + 1又2/9 - (-1又1/3) 的值。$
            # 結構：[負數帶分數] + [正數帶分數] - [負數帶分數]
            # 分數位置：3 個帶分數，每個含分子/分母

            # Step D2: 映射變數（分子/分母獨立）
            n1 = IntegerOps.random_nonzero(-99, 99)
            d1 = IntegerOps.random_nonzero(2, 10)
            n2 = IntegerOps.random_nonzero(-99, 99)
            d2 = IntegerOps.random_nonzero(2, 10)
            n3 = IntegerOps.random_nonzero(-99, 99)
            d3 = IntegerOps.random_nonzero(2, 10)

            # Step D3: 約分與驗證
            f1 = Fraction(n1, d1)
            f2 = Fraction(n2, d2)
            f3 = Fraction(n3, d3)

            # Step D4: 組 eval_str_init（純 Python 可計算）
            eval_str_init = f"Fraction({n1}, {d1}) + Fraction({n2}, {d2}) - Fraction({n3}, {d3})"

            # Step D5: 組 math_str（LaTeX 顯示）
            frac1 = FractionOps.to_latex(f1, mixed=True)
            frac2 = FractionOps.to_latex(f2, mixed=True)
            frac3 = FractionOps.to_latex(f3, mixed=True)

            math_str = f"(-{frac1}) + {frac2} - (-{frac3})"

            # Step D6: O(1) 智慧型倒算法與驗證
            ans_init = safe_eval(eval_str_init)
            if isinstance(ans_init, Fraction) and ans_init.denominator > 120:
                continue
            if isinstance(ans_init, Fraction) and abs(ans_init.numerator) > 120 or ans_init.denominator > 36:
                continue

            # Step D7: 重新組裝正式字串
            eval_str = f"Fraction({n1}, {d1}) + Fraction({n2}, {d2}) - Fraction({n3}, {d3})"
            math_str = f"(-{frac1}) + {frac2} - (-{frac3})"

            # Step D8: 美觀檢核
            if "}{1}" in math_str:
                continue

            # Step D9: 計算最終答案
            ans = safe_eval(eval_str)
            if isinstance(ans, Fraction):
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