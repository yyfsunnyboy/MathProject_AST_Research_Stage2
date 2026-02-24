# ==============================================================================
# ID: jh_數學2上_FourOperationsOfRadicals
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 13.80s | Tokens: In=759, Out=475
# Created At: 2026-02-24 15:47:07
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
import math

def generate(level=1, **kwargs):
    question = ''
    terms = []
    operations = ['+', '-']
    
    if level == 1:
        num_terms = random.randint(2, 4)
        for _ in range(num_terms):
            coeff = random.randint(1, 5)
            radicand = random.choice([2, 3, 5, 6, 7, 8, 10])
            terms.append(f"{coeff}\\sqrt{{{radicand}}}")
        question = ' + '.join(terms)
    elif level == 2:
        num_terms = random.randint(2, 3)
        for _ in range(num_terms):
            coeff = random.randint(1, 5)
            radicand = random.choice([2, 3, 5, 6, 7, 8, 10])
            terms.append(f"{coeff}\\sqrt{{{radicand}}}")
        question = ' + '.join(terms)
        if random.random() < 0.5:
            term1 = f"\\sqrt{{{random.choice([2, 3, 5, 6, 7, 8, 10])}}}"
            term2 = f"\\sqrt{{{random.choice([2, 3, 5, 6, 7, 8, 10])}}}"
            question += f" + ({term1} + {term2})(\\sqrt{{{random.choice([2, 3, 5, 6, 7, 8, 10])}}})" if random.random() < 0.5 else f" + ({term1} - {term2})(\\sqrt{{{random.choice([2, 3, 5, 6, 7, 8, 10])}}})"
    
    return {
        'question_text': f"化簡 $ {question} $",
        'answer': '',
        'correct_answer': 'placeholder',
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}