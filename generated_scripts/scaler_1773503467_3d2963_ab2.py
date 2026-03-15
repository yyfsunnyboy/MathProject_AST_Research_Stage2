import random
import math
from fractions import Fraction
# RadicalOps and FractionOps are injected automatically

def generate(level=1, **kwargs):
    # [分析1] 情境類型: F
    # [分析2] 根式項數: 2 項
    # [分析3] 運算符: ×
    # [分析4] 分數數量: 0 個
    # [分析5] 根號類型: r1=可化簡, r2=可化簡
    # [分析6] 生成策略: question_text 用 $...$，變數與答案共用同一組

    simplifiable = [8, 12, 18, 20, 24, 27, 32, 45, 48, 50, 72, 75]

    for _ in range(50):
        try:
            # Step A: 宣告所有隨機變數（一次性，f-string 裡禁止再呼叫 random）
            r1 = random.choice(simplifiable)
            r2 = random.choice(simplifiable)

            # Step B: 構造 question_text（必須包含 $...$，用上方同一組變數）
            question_text = f"化簡 $\\sqrt{{{r1}}} \\times \\sqrt{{{r2}}}$。"

            # Step C: 計算 correct_answer（依[分析1]情境選擇，只用一種計算方式）
            # 情境F → new_c, new_r = RadicalOps.simplify_term(coeff, radicand); correct_answer = RadicalOps.format_expression({new_r: new_c})
            new_c, new_r = RadicalOps.simplify_term(1, r1 * r2)
            correct_answer = RadicalOps.format_expression({new_r: new_c})

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