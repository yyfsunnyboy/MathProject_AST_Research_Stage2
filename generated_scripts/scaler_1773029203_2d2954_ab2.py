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
            # 運算子：2 個（+ 和 -），順序固定

            # Step D2: 映射變數（分子/分母各自獨立）
            n1 = IntegerOps.random_nonzero(-99, 99)
            d1 = IntegerOps.random_nonzero(2, 10)
            n2 = IntegerOps.random_nonzero(-99, 99)
            d2 = IntegerOps.random_nonzero(2, 10)
            n3 = IntegerOps.random_nonzero(-99, 99)
            d3 = IntegerOps.random_nonzero(2, 10)

            # Step D3: 確保分母非 0，且分子在 [-99, 99]
            # 若分母為 0 或分子超出範圍，重抽
            if d1 == 0 or d2 == 0 or d3 == 0:
                continue
            if abs(n1) > 99 or abs(n2) > 99 or abs(n3) > 99:
                continue

            # Step D4: 組 eval_str（純 Python 可計算）
            # 原題結構：(-a1 + a2 - (-a3)) → 但需轉為分數形式
            # 題目是：(-k1 + k2 - (-k3))，其中 k1, k2, k3 是帶分數
            # 分數轉換：Fraction(n, d) → 但需約分
            frac1 = Fraction(n1, d1)
            frac2 = Fraction(n2, d2)
            frac3 = Fraction(n3, d3)

            # 約分後轉為帶分數（若為假分數）
            def to_mixed(f):
                if f.denominator == 1:
                    return str(f.numerator)
                elif f.numerator == 0:
                    return "0"
                elif f.numerator < 0:
                    k = -f.numerator // f.denominator
                    r = f.numerator % f.denominator
                    if r == 0:
                        return f"-{k}"
                    else:
                        return f"-{k}\\frac{{{r}}}{{{f.denominator}}}"
                else:
                    k = f.numerator // f.denominator
                    r = f.numerator % f.denominator
                    if r == 0:
                        return str(k)
                    else:
                        return f"{k}\\frac{{{r}}}{{{f.denominator}}}"

            # Step D5: 組 math_str（LaTeX 顯示）
            # 原題結構：(-2又1/6) + 1又2/9 - (-1又1/3)
            # 題目結構：(-k1) + k2 - (-k3)
            # 顯示：帶分數轉 LaTeX
            math_str = f"(-{FractionOps.to_latex(frac1)}) + {FractionOps.to_latex(frac2)} - (-{FractionOps.to_latex(frac3)})"

            # Step D6: O(1) 智慧型倒算法與驗證
            # 建立 eval_str_init
            eval_str_init = f"Fraction({n1}, {d1}) + Fraction({n2}, {d2}) - Fraction({n3}, {d3})"
            ans_init = safe_eval(eval_str_init)

            # 檢查分母是否過大
            if isinstance(ans_init, Fraction) and ans_init.denominator > 120:
                continue

            # 檢查七年級友善範圍
            if isinstance(ans_init, Fraction):
                if abs(ans_init.numerator) > 120 or ans_init.denominator > 36:
                    continue

            # Step D7: 重新組裝正式字串
            eval_str = f"Fraction({n1}, {d1}) + Fraction({n2}, {d2}) - Fraction({n3}, {d3})"
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

            # Step D8: 美觀檢核
            if "}{1}" in math_str:
                continue

            # Step D9: 分子硬限制（已於 Step D3 檢查）

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