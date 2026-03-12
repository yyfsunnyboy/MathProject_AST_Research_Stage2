import random
import math
from fractions import Fraction
# RadicalOps and FractionOps are injected automatically

def generate(level=1, **kwargs):
    # Step 0: 解析題型結構 (必須先寫出這三行註解，確保你確實算過)
    # 根式項數 (即原題參與加減運算的根式有幾項): 2 項
    # 乘法分配律區塊: 0 (無)
    # 特殊結構: 分數係數 / 指數被開方數

    simplifiable = [8, 12, 18, 20, 24, 27, 32, 45, 48, 50, 72, 75]
    simple = [2, 3, 5, 7, 11]

    for _ in range(50):
        try:
            # 1. 根據 Step 0 的項數與區塊宣告對應數量的變數
            c1 = Fraction(1, 1)
            r1 = Fraction(random.choice(simplifiable), random.choice(simplifiable))
            c2 = Fraction(1, 1)
            r2 = Fraction(random.choice(simplifiable), random.choice(simplifiable))

            # 2. 組合題目字串
            q_part1 = RadicalOps.format_term_unsimplified(c1, r1, True)
            q_part2 = RadicalOps.format_term_unsimplified(c2, r2, False)
            question_text = f"計算 $({q_part1}) \\div ({q_part2})$ 的值。"

            # 3. 計算答案（純數值操作）
            final_terms = {}

            # 狀況 C: 若被開方數 (radicand) 是 Fraction (例如 \frac{\sqrt{A}}{\sqrt{B}}) 相乘除
            new_c, new_r = RadicalOps.simplify_term(c1 * c2, r1 / r2)
            final_terms[new_r] = final_terms.get(new_r, 0) + new_c

            correct_answer = RadicalOps.format_expression(final_terms)
            if correct_answer and correct_answer != '0':
                return {
                    'question_text': question_text,
                    'answer': '',
                    'correct_answer': correct_answer,
                    'mode': 1,
                    '_o1_healed': False
                }
        except Exception as e:
            with open('tmp_trace.txt', 'a') as f: traceback.print_exc(file=f)
            continue

    return {'question_text': 'Error', 'answer': '', 'correct_answer': '0', 'mode': 1}

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}