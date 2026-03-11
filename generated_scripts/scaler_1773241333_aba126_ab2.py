import random
import math
from fractions import Fraction

def generate(level=1, **kwargs):
    fmt = IntegerOps.fmt_num

    for _ in range(200):
        # Step D1: 原題結構為 [(-20)+(-10)]÷(-5)×3 → 4 個數字，3 個運算子，1 個中括號
        # Step D2: 映射變數 v1, v2, v3, v4 → 對應原題位置
        v1 = IntegerOps.random_nonzero(-100, -1)  # 第一個負數
        v2 = IntegerOps.random_nonzero(-10, -1)   # 第二個負數
        v3 = IntegerOps.random_nonzero(-15, -1)   # 除數（負數）
        v4 = IntegerOps.random_nonzero(1, 15)     # 乘數（正數）

        # Step D3: 結構固定，運算順序固定：[v1 + v2] ÷ v3 × v4
        # Step D4: 計算分子與分母（整數值）
        numerator = v1 + v2
        denominator = v3 * v4

        # Step D5: 整除預檢
        if denominator == 0 or abs(numerator) % abs(denominator) != 0:
            continue

        final_ans = abs(numerator) // abs(denominator)
        # 計算符號：若分母為負，結果取負號（但原題中除數為負，乘數為正，結果應為正）
        # 但實際上：[負+負] ÷ 負 × 正 = 正 → 所以最終符號由分子分母共同決定
        # 但我們在整除後直接取絕對值再套正負號，更安全
        # 這裡直接用最終結果的符號：若原式為負，則結果為負
        # 但實際上：[v1+v2] 是負，v3 是負，v4 是正 → 負 ÷ 負 = 正 → 正 × 正 = 正
        # 所以最終結果為正 → 不需要調整符號

        # Step D6: 組裝 eval_str 與 math_str
        eval_str = f"({v1}+{v2})/{v3}*{v4}"
        math_str = f"\\left[\\left({fmt(v1)}+{fmt(v2)}\\right}\\right]\\div {fmt(v3)} \\times {fmt(v4)}"

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