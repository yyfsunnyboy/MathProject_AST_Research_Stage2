import random
import math
from fractions import Fraction

def generate(level=1, **kwargs):
    # 變數個數: 2 個
    # 運算符號數與種類: 1 個 (分別為 plus)
    # 特殊結構: 無 / 絕對值 / 中括號

    fmt = IntegerOps.fmt_num

    for _ in range(200):
        # 1) 依 Step 0 解析出的「變數個數」，嚴格依序宣告對應數量的變數！
        # 【最高禁令】原題有幾個參與運算的數字，你就只能生成幾個變數！
        # 【致命錯誤防範】絕對禁止將變數寫死成固定數字（如 v1 = 5）！所有數值必須使用 IntegerOps.random_nonzero 動態生成！
        v1 = IntegerOps.random_nonzero(-100, 100)
        v2 = IntegerOps.random_nonzero(-100, 100)

        # 2) 直接計算分子/分母整數值（不用 safe_eval，不用 Fraction 縮放）
        # 依據上方宣告的變數，組合出分子分母的算式
        numerator = v1 + v2
        denominator = 1  # 無分母，直接整除

        # 3) 整除預檢：用 % 判斷
        if denominator == 0 or abs(numerator) % abs(denominator) != 0:
            continue

        final_ans = abs(numerator) // abs(denominator)
        # 若分母為負，結果取負號（依題目運算方向而定）
        # 但分母固定為 1，無需調整

        # 4) 組裝 eval_str（純運算）與 math_str（LaTeX 顯示）
        # ★ 你必須宣告 eval_str 與 math_str 這兩個變數！
        # 【最高禁令】必須按照原題的運算子與數字個數！嚴禁無腦照抄 5個變數的範例！
        eval_str = f"{v1} + {v2}"
        math_str = f"\\left({fmt(v1)}\\right) + \\left({fmt(v2)}\\right)"

        ans = IntegerOps.safe_eval(eval_str)
        if abs(ans - round(ans)) < 1e-6:
            return {
                'question_text': '計算 $' + math_str + '$ 的值。',
                'answer': '',
                'correct_answer': str(int(round(ans))),
                'mode': 1,
            }

    return {'question_text': 'Error', 'answer': '', 'correct_answer': '0', 'mode': 1}

def check(user_answer, correct_answer):
    try:
        if str(user_answer).strip() == str(correct_answer).strip():
            return {'correct': True, 'result': '正確'}
        if abs(float(user_answer) - float(correct_answer)) < 1e-6:
            return {'correct': True, 'result': '正確'}
    except Exception:
        pass
    return {'correct': False, 'result': '錯誤'}