import random
import math
from fractions import Fraction
# RadicalOps and FractionOps are injected automatically

def generate(level=1, **kwargs):
    # Step 0: 解析題型結構 (必須先寫出這三行註解，確保你確實算過)
    # 根式項數 (即原題參與加減運算的根式有幾項): 3 項
    # 乘法分配律區塊: 1 組

    simplifiable = [8, 12, 18, 20, 24, 27, 32, 45, 48, 50, 72, 75]
    simple = [2, 3, 5, 7, 11]

    for _ in range(50):
        try:
            # 1. 根據 Step 0 的項數與區塊宣告對應數量的變數
            # 【最高禁令】原題有幾項根式、是否有乘法分配律區塊，你就必須 100% 照做宣告對應的變數！
            # 若有分數係數，請使用 Fraction宣告，例: c1 = Fraction(random.randint(-5, -1), random.randint(2, 5))
            # 若無分數係數，請宣告整數，例: c1 = random.choice([-3, -2, 2, 3, 4, 5])
            # r1 = random.choice(simple)
            # r2 = random.choice(simplifiable)
            c1 = random.choice([-3, -2, 2, 3, 4, 5])
            r1 = random.choice(simple)
            c2 = random.choice([-3, -2, 2, 3, 4, 5])
            r2 = random.choice(simplifiable)
            c3 = random.choice([-3, -2, 2, 3, 4, 5])
            r3 = random.choice(simplifiable)
            c_mul = random.choice([-3, -2, 2, 3, 4, 5])
            r_mul = random.choice(simple)

            # 2. 組合題目字串
            # ★ 你必須宣告 question_text 這個變數！
            q_part1 = RadicalOps.format_term_unsimplified(c1, r1, True)
            q_part2 = RadicalOps.format_term_unsimplified(c2, r2, False)
            q_part3 = RadicalOps.format_term_unsimplified(c3, r3, False)
            q_mul = RadicalOps.format_term_unsimplified(c_mul, r_mul, True)
            question_text = f"化簡 $({q_part1} + {q_part2} - {q_part3}) + {q_mul}$"

            # 3. 計算答案（純數值操作）
            final_terms = {}

            # 狀況 A: 若是單純加減法
            new_c1, new_r1 = RadicalOps.simplify_term(c1, r1)
            final_terms[new_r1] = final_terms.get(new_r1, 0) + new_c1

            new_c2, new_r2 = RadicalOps.simplify_term(c2, r2)
            final_terms[new_r2] = final_terms.get(new_r2, 0) + new_c2

            new_c3, new_r3 = RadicalOps.simplify_term(c3, r3)
            final_terms[new_r3] = final_terms.get(new_r3, 0) + new_c3

            # 狀況 B: 若是根式相乘 ( c1\sqrt{r1} * c2\sqrt{r2} )
            comb_c = c_mul
            comb_r = r_mul
            new_c, new_r = RadicalOps.simplify_term(comb_c, comb_r)
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
        except Exception:
            continue

    return {'question_text': 'Error', 'answer': '', 'correct_answer': '0', 'mode': 1}

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}