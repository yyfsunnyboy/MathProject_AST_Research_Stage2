import random
import math
from fractions import Fraction


def generate(level=1, **kwargs):
    for _ in range(30):
        try:
            # Step D1: 讀取目標題型結構
            # 原題：計算 $(-2又1/6) + 1又2/9 - (-1又1/3) 的值。$
            # 結構：[負數帶分數] + [正數帶分數] - [負數帶分數]
            # 分數數量：3 個，每個含分子/分母
            # 運算子：2 個（+、-），順序固定

            # Step D2: 映射變數
            # n1, d1 → 分子/分母 for 第一個帶分數
            # n2, d2 → 分子/分母 for 第二個帶分數
            # n3, d3 → 分子/分母 for 第三個帶分數

            # Step D3: 生成值（分母非0，分子在[-99,99]）
            n1 = IntegerOps.random_nonzero(-99, 99)
            d1 = IntegerOps.random_nonzero(2, 10)
            n2 = IntegerOps.random_nonzero(-99, 99)
            d2 = IntegerOps.random_nonzero(2, 10)
            n3 = IntegerOps.random_nonzero(-99, 99)
            d3 = IntegerOps.random_nonzero(2, 10)

            # Step D4: 建立 eval_str_init（純 Python 可計算）
            # 原題結構：(-a1) + a2 - (-a3)
            # a1 = n1/d1, a2 = n2/d2, a3 = n3/d3
            eval_str_init = f"Fraction({n1}, {d1}) + Fraction({n2}, {d2}) - Fraction({n3}, {d3})"

            # Step D5: 計算初始答案（安全評估）
            ans_init = safe_eval(eval_str_init)

            # Step D6: O(1) 智慧型倒算法與驗證
            if isinstance(ans_init, Fraction) and ans_init.denominator > 120:
                continue
            if isinstance(ans_init, Fraction) and abs(ans_init.numerator) > 120 or ans_init.denominator > 36:
                continue

            # Step D7: 重新組裝正式字串
            # 生成 eval_str（純 Python 計算字串）
            eval_str = f"Fraction({n1}, {d1}) + Fraction({n2}, {d2}) - Fraction({n3}, {d3})"

            # 生成 math_str（LaTeX 顯示字串）
            frac1 = FractionOps.to_latex(Fraction(n1, d1))
            frac2 = FractionOps.to_latex(Fraction(n2, d2))
            frac3 = FractionOps.to_latex(Fraction(n3, d3))

            math_str = f"({frac1}) + ({frac2}) - ({frac3})"

            # Step D8: 美觀檢核
            if "}{1}" in math_str:
                continue

            # Step D9: 最終計算與約分
            ans = safe_eval(eval_str)
            if isinstance(ans, Fraction):
                f_ans = Fraction(ans).limit_denominator()
                if f_ans.denominator == 1:
                    correct_answer = str(f_ans.numerator)
                else:
                    correct_answer = f"{f_ans.numerator}/{f_ans.denominator}"
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