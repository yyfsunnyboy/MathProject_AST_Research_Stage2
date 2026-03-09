import random
import math
from fractions import Fraction

def generate(level=1, **kwargs):
    fmt = IntegerOps.fmt_num

    for _ in range(25):
        # 原題結構：| 8×(-2)-5 | ÷ 7×(-3)
        # 變數映射：v1=8, v2=-2, v3=5, v4=7, v5=-3
        # 結構：| v1×v2 - v3 | ÷ v4×v5
        # 運算符：×, -, | |, ÷, ×
        # 數字數量：5
        # 運算子數量：5（×, -, | |, ÷, ×）→ 但 | | 是結構符號，不計入運算子，實際運算子為 4 個：×, -, ÷, ×
        # 重新解析：實際運算符為 4 個：×, -, ÷, × → 但題目中「÷」是二元運算，「×」出現兩次 → 總運算子數 = 4
        # 絕對值區塊：1 個，內部：v1×v2 - v3 → 數字 3 個，運算子 2 個（×, -）

        # Step D1: 建立結構模板（只替換數字）
        # Step D2: 映射變數
        v1 = IntegerOps.random_nonzero(1, 100)  # 第一個數，正數 [1,100]
        v2 = IntegerOps.random_nonzero(-10, -1)  # 第二個數，負數 [-10,-1]
        v3 = IntegerOps.random_nonzero(1, 10)    # 第三個數，正數 [1,10]
        v4 = IntegerOps.random_nonzero(1, 15)    # 第四個數，正數 [1,15]
        v5 = IntegerOps.random_nonzero(-15, -1)  # 第五個數，負數 [-15,-1]

        # Step D4: 組出 eval_str（純 Python 可計算）
        eval_str = "abs(v1 * v2 - v3) / (v4 * v5)"

        # Step D5: 組出 math_str（LaTeX 顯示）
        math_str = f"\\left| {fmt(v1)} \\times {fmt(v2)} - {fmt(v3)} \\right| \\div {fmt(v4)} \\times {fmt(v5)}"

        # Step D6: O(1) 智慧型倒算法與驗證
        try:
            # 預先計算，保留分母
            ans_init = IntegerOps.safe_eval(eval_str.replace('v1', str(v1)).replace('v2', str(v2)).replace('v3', str(v3)).replace('v4', str(v4)).replace('v5', str(v5)))
            if isinstance(ans_init, Fraction) and ans_init.denominator != 1:
                # 強制整除：將分母乘回 v1
                if ans_init.denominator > 1000:
                    continue
                v1 = v1 * ans_init.denominator
                # 重新組裝 eval_str
                eval_str = "abs(v1 * v2 - v3) / (v4 * v5)"
                # 重新組裝 math_str
                math_str = f"\\left| {fmt(v1)} \\times {fmt(v2)} - {fmt(v3)} \\right| \\div {fmt(v4)} \\times {fmt(v5)}"
                # 重新計算
                ans = IntegerOps.safe_eval(eval_str.replace('v1', str(v1)).replace('v2', str(v2)).replace('v3', str(v3)).replace('v4', str(v4)).replace('v5', str(v5)))
                if abs(ans - round(ans)) < 1e-6:
                    final_ans = int(round(ans))
                    return {
                        'question_text': '計算 $' + math_str + '$ 的值。',
                        'answer': '',
                        'correct_answer': str(final_ans),
                        'mode': 1,
                        '_o1_healed': True
                    }
            else:
                ans = IntegerOps.safe_eval(eval_str.replace('v1', str(v1)).replace('v2', str(v2)).replace('v3', str(v3)).replace('v4', str(v4)).replace('v5', str(v5)))
                if abs(ans - round(ans)) < 1e-6:
                    final_ans = int(round(ans))
                    return {
                        'question_text': '計算 $' + math_str + '$ 的值。',
                        'answer': '',
                        'correct_answer': str(final_ans),
                        'mode': 1,
                        '_o1_healed': False
                    }
        except Exception:
            continue

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