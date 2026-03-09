import random
import math
from fractions import Fraction


def generate(level=1, **kwargs):
    for _ in range(30):
        try:
            # Step D1: 讀取目標題型結構
            # 原題：計算 $(-2又1/6) + 1又2/9 - (-1又1/3) 的值。$
            # 結構：[負數帶分數] + [正數帶分數] - [負數帶分數]
            # 分數位置：3 個帶分數，每一個含分子/分母

            # Step D2: 映射變數
            # n1, d1, n2, d2, n3, d3 → 分子/分母
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

            # Step D4: 建立 eval_str_init（純 Python 可計算）
            eval_str_init = f"Fraction({n1}, {d1}) + Fraction({n2}, {d2}) - Fraction({n3}, {d3})"

            # Step D5: 計算初始答案
            ans_init = safe_eval(eval_str_init)

            # Step D6: O(1) 智慧型倒算法與驗證
            if isinstance(ans_init, Fraction) and ans_init.denominator > 120:
                continue
            if isinstance(ans_init, Fraction) and abs(ans_init.numerator) > 120 or ans_init.denominator > 36:
                continue

            # Step D7: 生成正式 eval_str 與 math_str
            # 保留分數拓撲，轉為 LaTeX 顯示
            f1_latex = FractionOps.to_latex(f1)
            f2_latex = FractionOps.to_latex(f2)
            f3_latex = FractionOps.to_latex(f3)

            # 題面結構：[負數帶分數] + [正數帶分數] - [負數帶分數]
            # 負號處理：若 f1 < 0 → -f1_latex，否則 f1_latex
            # 同理 f3 → -f3_latex
            math_str = f"(-{f1_latex}) + {f2_latex} - (-{f3_latex})"

            # Step D8: 最終答案格式化
            ans = safe_eval(eval_str_init)
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

            # Step D9: 美觀檢核
            if "}{1}" in math_str:
                continue
            if "1/1" in math_str:
                continue

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