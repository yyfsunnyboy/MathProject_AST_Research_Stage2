import random
import math
from fractions import Fraction

def generate(level=1, **kwargs):
    simplifiable = [8, 12, 18, 20, 24, 27, 32, 45, 48, 50, 72, 75]
    simple = [2, 3, 5, 7, 11]

    for _ in range(50):
        try:
            # Step A: 宣告所有隨機變數（一次性，f-string 裡禁止再呼叫 random）
            context = {
                'r1': random.choice(simple),
                'r2': random.choice(simplifiable),
                'c1': random.choice(simple),
                'c2': random.choice(simplifiable),
                'op': random.choice(['times', 'divide']),
                'frac_count': random.choice([0, 1, 2]),
                'level': level
            }

            # Step B: 構造 question_text（必須包含 $...$，用上方同一組變數）
            if context['frac_count'] == 0:
                if context['op'] == 'times':
                    question_text = f"化簡 $\\sqrt{{{context['r1']}}} \\times \\sqrt{{{context['r2']}}}$。"
                else:
                    question_text = f"化簡 $\\sqrt{{{context['r1']}}} \\div \\sqrt{{{context['r2']}}}$。"
            elif context['frac_count'] == 1:
                if context['op'] == 'times':
                    question_text = f"化簡 $\\frac{{\\sqrt{{{context['r1']}}}}}{{\\sqrt{{{context['r2']}}}}} \\times \\sqrt{{{context['c1']}}}$。"
                else:
                    question_text = f"化簡 $\\frac{{\\sqrt{{{context['r1']}}}}}{{\\sqrt{{{context['r2']}}}}} \\div \\sqrt{{{context['c1']}}}$。"
            else:  # frac_count == 2
                if context['op'] == 'times':
                    question_text = f"化簡 $\\frac{{\\sqrt{{{context['r1']}}}}}{{\\sqrt{{{context['r2']}}}}} \\times \\frac{{\\sqrt{{{context['c1']}}}}}{{\\sqrt{{{context['c2']}}}}}$。"
                else:
                    question_text = f"化簡 $\\frac{{\\sqrt{{{context['r1']}}}}}{{\\sqrt{{{context['r2']}}}}} \\div \\frac{{\\sqrt{{{context['c1']}}}}}{{\\sqrt{{{context['c2']}}}}}$。"

            # Step C: 計算 correct_answer（依情境選擇）
            if context['frac_count'] == 0:
                # 情境A/B/D → 用 final_terms = {}; ... ; correct_answer = RadicalOps.format_expression(final_terms)
                if context['op'] == 'times':
                    final_terms = {}
                    r1 = context['r1']
                    r2 = context['r2']
                    # 簡化根式乘法：√a × √b = √(a×b)
                    product = r1 * r2
                    # 簡化 √product
                    root = RadicalOps.simplify_root(product)
                    final_terms[root] = 1
                    correct_answer = RadicalOps.format_expression(final_terms)
                else:
                    final_terms = {}
                    r1 = context['r1']
                    r2 = context['r2']
                    # 簡化根式除法：√a ÷ √b = √(a/b)
                    quotient = r1 / r2
                    # 簡化 √quotient
                    root = RadicalOps.simplify_root(quotient)
                    final_terms[root] = 1
                    correct_answer = RadicalOps.format_expression(final_terms)
            elif context['frac_count'] == 1:
                # 情境C/E/G → correct_answer = RadicalOps.format_expression({...}, denominator=denom)
                if context['op'] == 'times':
                    final_terms = {}
                    r1 = context['r1']
                    r2 = context['r2']
                    c1 = context['c1']
                    # 簡化 (√r1 / √r2) × √c1 = √(r1 × c1) / √r2
                    numerator = r1 * c1
                    denominator = r2
                    # 簡化 √(numerator/denominator)
                    root = RadicalOps.simplify_root(numerator / denominator)
                    final_terms[root] = 1
                    correct_answer = RadicalOps.format_expression(final_terms)
                else:
                    final_terms = {}
                    r1 = context['r1']
                    r2 = context['r2']
                    c1 = context['c1']
                    # 簡化 (√r1 / √r2) ÷ √c1 = √(r1) / (√r2 × √c1) = √(r1) / √(r2 × c1)
                    denominator = r2 * c1
                    root = RadicalOps.simplify_root(r1 / denominator)
                    final_terms[root] = 1
                    correct_answer = RadicalOps.format_expression(final_terms)
            else:  # frac_count == 2
                # 情境C/E/G → correct_answer = RadicalOps.format_expression({...}, denominator=denom)
                if context['op'] == 'times':
                    final_terms = {}
                    r1 = context['r1']
                    r2 = context['r2']
                    c1 = context['c1']
                    c2 = context['c2']
                    # 簡化 (√r1 / √r2) × (√c1 / √c2) = √(r1 × c1) / √(r2 × c2)
                    numerator = r1 * c1
                    denominator = r2 * c2
                    root = RadicalOps.simplify_root(numerator / denominator)
                    final_terms[root] = 1
                    correct_answer = RadicalOps.format_expression(final_terms)
                else:
                    final_terms = {}
                    r1 = context['r1']
                    r2 = context['r2']
                    c1 = context['c1']
                    c2 = context['c2']
                    # 簡化 (√r1 / √r2) ÷ (√c1 / √c2) = √(r1 × c2) / √(r2 × c1)
                    numerator = r1 * c2
                    denominator = r2 * c1
                    root = RadicalOps.simplify_root(numerator / denominator)
                    final_terms[root] = 1
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