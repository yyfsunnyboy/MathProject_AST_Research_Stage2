# ==============================================================================
# ID: jh_數學2上_FourOperationsOfRadicals
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 7.32s | Tokens: In=759, Out=305
# Created At: 2026-02-24 15:55:51
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
import math

def generate(level=1, **kwargs):
    question_text = ""
    answer = ""
    correct_answer = ""
    mode = 1
    operations = ['+', '-']
    radicals = [random.randint(2, 20) for _ in range(4)]
    coefficients = [random.randint(1, 5) for _ in range(4)]
    terms = []
    for i in range(2):
        term = f"{coefficients[i]}\\sqrt{{{radicals[i]}}}"
        terms.append(term)
    part1 = " + ".join(terms)
    part2 = f"({terms[2]}{random.choice(operations)}{terms[3]})"
    question_text = f"化簡 $({part1}) + ({part2})$"
    correct_answer = f"{sum(coefficients[:2])}\\sqrt{{{radicals[0]}}} + {sum(coefficients[2:])}\\sqrt{{{radicals[2]}}} + {coefficients[2] * coefficients[3]}\\sqrt{{{radicals[2] * radicals[3]}}}"
    return {'question_text': question_text, 'answer': answer, 'correct_answer': correct_answer, 'mode': mode}

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}