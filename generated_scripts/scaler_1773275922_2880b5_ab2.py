import random
import math
from fractions import Fraction


def generate(level=1, **kwargs):
    # Step 0: 解析題型結構 (必須先寫出這三行註解，確保你確實算過)
    # 分數個數 (即原題參與運算的分數數量): 3 個
    # 運算符號數與種類: 5 個 (分別為 +, -, ×, ÷)
    # 特殊結構: 無 / 絕對值 / 中括號
    
    for _ in range(100):  # 多迭代確保一定能找到樣本
        try:
            # Step 1: 依 Step 0 的「分數個數」生成對應長度的變數
            # 【最高禁令】原題有幾個參與運算的數字，你就只能生成幾組分子分母！絕對禁止直接抄寫 3個分數！
            n1 = IntegerOps.random_nonzero(-99, 99)
            d1 = IntegerOps.random_nonzero(1, 100)
            n2 = IntegerOps.random_nonzero(-99, 99)
            d2 = IntegerOps.random_nonzero(1, 100)
            n3 = IntegerOps.random_nonzero(-99, 99)
            d3 = IntegerOps.random_nonzero(1, 100)
            
            # Step 2: 用 safe_eval 預計算答案（Fraction 精確計算）
            # 【最高禁令】必須按照原題的運算子！
            eval_str = f"Fraction({n1}, {d1}) + Fraction({n2}, {d2}) - Fraction({n3}, {d3})"
            ans = safe_eval(eval_str)

            # Step 3: D6 單一過濾（閾值 120，無運算子優先級陷阱）
            if not isinstance(ans, Fraction) or abs(ans.numerator) > 120 or ans.denominator > 120:
                continue

            # Step 4: 組裝 math_str（LaTeX 顯示，關鍵：mixed=True 強制帶分數格式）
            # ★ 你必須宣告 math_str 這個變數！
            f1_str = FractionOps.to_latex(Fraction(n1, d1), mixed=True)
            f2_str = FractionOps.to_latex(Fraction(n2, d2), mixed=True)
            f3_str = FractionOps.to_latex(Fraction(n3, d3), mixed=True)
            math_str = f"({f1_str}) + ({f2_str}) - ({f3_str})"

            # Step 5: 美觀檢核
            if "}{1}" in math_str:
                continue

            # Step 6: 格式化答案（分母為 1 時顯示整數）
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