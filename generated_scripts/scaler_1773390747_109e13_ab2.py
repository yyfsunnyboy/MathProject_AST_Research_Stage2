import random
import math
from fractions import Fraction
# RadicalOps and FractionOps are injected automatically

def generate(level=1, **kwargs):
    # Step 0: 解析題型結構 (必須先寫出這三行註解，確保你確實算過)
    # 根式項數 (即原題參與加減運算的根式有幾項): 2 項
    # 乘法分配律區塊: 0 (無)

    simplifiable = [2, 3, 5, 6, 7, 10, 11, 13, 14, 15, 17, 19, 21, 22, 23, 26, 29, 30, 31, 33, 34, 35, 37, 38, 39, 41, 42]
    simple = [2, 3, 5, 7, 11]

    for _ in range(50):
        try:
            # 1. 根據 Step 0 的項數與區塊宣告對應數量的變數
            # 【最高禁令】原題有幾項根式、是否有乘法分配律區塊，你就必須 100% 照做宣告對應的變數！
            # 若有分數係數，請使用 Fraction宣告，例: c1 = Fraction(random.randint(-5, -1), random.randint(2, 5))
            # 若無分數係數，請宣告整數，例: c1 = random.choice([-3, -2, 2, 3, 4, 5])
            # r1 = random.choice(simple)
            # r2 = random.choice(simplifiable)
            
            # 2. 組合題目字串
            # ★ 你必須宣告 question_text 這個變數！
            # 若原題包含乘除運算，必須構造出正確的 LaTeX 顯示：
            # q_part1 = RadicalOps.format_term_unsimplified(c1, r1, True)   # is_first=True 避免產生 + 號
            # q_part2 = RadicalOps.format_term_unsimplified(c2, r2, True)   # 乘除運算的後項也視為獨立項，設為 True
            # 
            # 若係數為負，手動加入圓括號；若為正，則不加括號：
            # str_p1 = f"({q_part1})" if c1 < 0 else q_part1
            # str_p2 = f"({q_part2})" if c2 < 0 else q_part2
            # question_text = f"計算 ${str_p1} \\times {str_p2}$ 的值。"
            question_text = f"計算 $\\sqrt{{{random.choice(simple)}}} \\div \\sqrt{{{random.choice(simple)}}}$ 的值。"
            
            # 3. 計算答案（純數值操作）
            final_terms = {}
            
            # 狀況 A: 若是單純加減法
            # RadicalOps.add_term(final_terms, c1, r1)
            
            # 狀況 B: 若是根式相乘 ( c1\sqrt{r1} * c2\sqrt{r2} )
            # new_c, new_r = RadicalOps.mul_terms(c1, r1, c2, r2)
            # RadicalOps.add_term(final_terms, new_c, new_r)
            
            # 狀況 C: 若是根式相除 ( c1\sqrt{r1} ÷ c2\sqrt{r2} )
            # [倒算法] 先決定除數與商，再反推被除數，確保能整除
            # c2 = random.choice([-3, -2, 2, 3])
            # r2 = random.choice(simple)
            # k_c = random.choice([-4, -3, -2, 2, 3, 4]) # 商的係數
            # k_r = random.choice(simple + [4, 9])      # 商的被開方數
            # c1 = c2 * k_c
            # r1 = r2 * k_r
            # new_c, new_r = RadicalOps.div_terms(c1, r1, c2, r2) # 驗算
            # RadicalOps.add_term(final_terms, new_c, new_r)
            
            # 狀況 D: 若被開方數 (radicand) 是 Fraction (例如 \frac{\sqrt{A}}{\sqrt{B}}) 相除
            # new_c, new_r = RadicalOps.div_terms(c1, r1, c2, r2)
            # RadicalOps.add_term(final_terms, new_c, new_r)

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