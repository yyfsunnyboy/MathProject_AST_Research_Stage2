# ==============================================================================
# ID: jh_數學2上_FourOperationsOfRadicals
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 12.20s | Tokens: In=759, Out=281
# Created At: 2026-02-23 23:22:23
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
        sign = random.choice(operations)
        coeff = random.randint(1, 5)
        radicand = random.randint(2, 20)
        terms.append(f"{sign}{coeff}\\sqrt{{{radicand}}}")
    question += "(" + "+".join(terms[1:]) + ")"
    terms = []
    for _ in range(2):
        sign = random.choice(operations)
        coeff = random.randint(1, 5)
        radicand = random.randint(2, 20)
        terms.append(f"{sign}{coeff}\\sqrt{{{radicand}}}")
    question += "+(" + "+".join(terms) + ")"
    answer = ""
    correct_answer = ""
    return {
        'question_text': f"化簡 ${question}$",
        'answer': answer,
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}