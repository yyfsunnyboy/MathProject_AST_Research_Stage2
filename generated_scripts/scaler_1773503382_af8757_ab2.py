import random
import math
from fractions import Fraction

def generate(level=1, **kwargs):
    simplifiable = [8, 12, 18, 20, 24, 27, 32, 45, 48, 50, 72, 75]
    simple = [2, 3, 5, 7, 11]

    for _ in range(50):
        try:
            r1 = random.choice(simplifiable)
            r2 = random.choice(simplifiable)
            c1 = random.choice(simple)
            c2 = random.choice(simple)

            question_text = f"化簡 $\\sqrt{{{r1}}} \\times \\sqrt{{{r2}}}$。"

            new_c1, new_r1 = RadicalOps.simplify_term(1, r1 * r2)
            correct_answer = RadicalOps.format_expression({new_r1: new_c1})

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