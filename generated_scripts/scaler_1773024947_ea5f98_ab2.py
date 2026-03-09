import random
import math
from fractions import Fraction


def generate(level=1, **kwargs):
    for _ in range(30):
        try:
            # Step D1: 讀取目標題型結構
            # 原題：計算 $(-2又1/6) + 1又2/9 - (-1又1/3) 的值。$
            # 結構：[負數帶分數] + [正數帶分數] - [負數帶分數]
            # 分數數量：3 個分數（每個帶分數含 1 個分數）
            # 運算子：2 個（+ 和 -）
            # 小數：無

            # Step D2: 映射變數（分子/分母各自獨立）
            # 原題分數結構：
            #   第1項：-2又1/6 → 分子: -13, 分母: 6
            #   第2項：1又2/9 → 分子: 11, 分母: 9
            #   第3項：-(-1又1/3) → 等價於 +1又1/3 → 分子: 4, 分母: 3

            # Step D3: 生成值（分母非0，分子在[-99,99]）
            n1 = IntegerOps.random_nonzero(-99, 99)
            d1 = IntegerOps.random_nonzero(2, 10)
            n2 = IntegerOps.random_nonzero(-99, 99)
            d2 = IntegerOps.random_nonzero(2, 10)
            n3 = IntegerOps.random_nonzero(-99, 99)
            d3 = IntegerOps.random_nonzero(2, 10)

            # Step D4: 組 eval_str（純 Python 可計算）
            eval_str_init = f"Fraction({n1}, {d1}) + Fraction({n2}, {d2}) - Fraction({n3}, {d3})"
            ans_init = safe_eval(eval_str_init)

            # Step D5: O(1) 智慧型倒算法與驗證
            if isinstance(ans_init, Fraction) and ans_init.denominator > 120:
                continue
            if isinstance(ans_init, Fraction) and abs(ans_init.numerator) > 120 or ans_init.denominator > 36:
                continue

            # Step D6: 重新組裝正式字串
            # 分數轉 LaTeX（使用 FractionOps.to_latex）
            frac1 = FractionOps.to_latex(Fraction(n1, d1))
            frac2 = FractionOps.to_latex(Fraction(n2, d2))
            frac3 = FractionOps.to_latex(Fraction(n3, d3))

            # 帶分數轉換（若為假分數則轉為帶分數）
            def to_mixed(frac):
                if frac.denominator == 1:
                    return str(frac.numerator)
                elif frac.numerator == 0:
                    return "0"
                elif frac.numerator < 0:
                    k = -frac.numerator // frac.denominator
                    r = -frac.numerator % frac.denominator
                    if r == 0:
                        return f"-{k}"
                    else:
                        return f"-{k}\\frac{{{r}}}{{{frac.denominator}}}"
                else:
                    k = frac.numerator // frac.denominator
                    r = frac.numerator % frac.denominator
                    if r == 0:
                        return str(k)
                    else:
                        return f"{k}\\frac{{{r}}}{{{frac.denominator}}}"

            # 題目顯示：帶分數形式（需轉為 LaTeX）
            math_str = f"({to_mixed(Fraction(n1, d1))}) + ({to_mixed(Fraction(n2, d2))}) - ({to_mixed(Fraction(n3, d3))})"

            # Step D7: 回傳
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