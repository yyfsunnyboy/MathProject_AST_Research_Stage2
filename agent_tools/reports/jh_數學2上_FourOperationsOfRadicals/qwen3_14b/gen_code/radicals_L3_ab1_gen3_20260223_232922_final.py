# ==============================================================================
# ID: jh_數學2上_FourOperationsOfRadicals
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 15.06s | Tokens: In=759, Out=346
# Created At: 2026-02-23 23:29:22
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
import math

def generate(level=1, **kwargs):
    question = ""
    terms = []
    operations = ["+", "-"]
    num_terms = random.randint(2, 4)
    for _ in range(num_terms):
        if random.random() < 0.5:
            coeff = random.randint(1, 5)
            radicand = random.randint(2, 20)
            terms.append(f"{coeff}\\sqrt{{{radicand}}}")
        else:
            coeff = random.randint(1, 5)
            radicand = random.randint(2, 20)
            terms.append(f"\\sqrt{{{radicand}}}")
    question += " + ".join(terms)
    if random.random() < 0.5:
        coeff = random.randint(1, 5)
        radicand = random.randint(2, 20)
        question += f" + {coeff}\\sqrt{{{radicand}}}"
    else:
        coeff = random.randint(1, 5)
        radicand = random.randint(2, 20)
        question += f" - {coeff}\\sqrt{{{radicand}}}"
    question = f"化簡 $({question})$"
    answer = ""
    correct_answer = ""
    return {
        'question_text': question,
        'answer': answer,
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}