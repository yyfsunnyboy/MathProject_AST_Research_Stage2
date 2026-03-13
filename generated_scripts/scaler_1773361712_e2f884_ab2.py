import random
import math
from fractions import Fraction
# RadicalOps and FractionOps are injected automatically

def generate(level=1, **kwargs):
    # Step 0: 解析題型結構 (必須先寫出這三行註解，確保你確實算過)
    # 根式項數 (即原題參與加減運算的根式有幾項): 2 項
    # 乘法分配律區塊: 1 (無 / 幾組)

    simplifiable = [8, 12, 18, 20, 24, 27, 32, 45, 48, 50, 72, 75]
    simple = [2, 3, 5, 7, 11]

    for _ in range(50):
        try:
            # 1. 根據 Step 0 的項數與區塊宣告對應數量的變數
            c1 = random.choice([-5, -4, -3, -2, 2, 3, 4, 5])
            r1 = random.choice(simplifiable)
            c2 = random.choice([-5, -4, -3, -2, 2, 3, 4, 5])
            r2 = random.choice(simplifiable)

            # 2. 組合題目字串
            q_part1 = RadicalOps.format_term_unsimplified(c1, r1, True)
            q_part2 = RadicalOps.format_term_unsimplified(c2, r2, False)
            question_text = f"計算 $({q_part1}) \\times ({q_part2})$ 的值。"

            # 3. 計算答案（純數值操作）
            final_terms = {}

            # 狀況 B: 若是根式相乘 ( c1\sqrt{r1} * c2\sqrt{r2} )
            new_c, new_r = RadicalOps.mul_terms(c1, r1, c2, r2)
            RadicalOps.add_term(final_terms, new_c, new_r)

            correct_answer = RadicalOps.format_expression(final_terms)
            if correct_answer and correct_answer != '0':
                return {
                    'question_text': question_text,
                    'answer': '',
                    'correct_answer': correct_answer,
                    'mode': 1,
                    '_o1_healed': False
                }
        except Exception:
            continue

    return {'question_text': 'Error', 'answer': '', 'correct_answer': '0', 'mode': 1}

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}