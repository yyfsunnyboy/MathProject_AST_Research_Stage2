# ==============================================================================
# ID: jh_數學2上_FourOperationsOfRadicals
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 87.95s | Tokens: In=753, Out=1336
# Created At: 2026-02-20 02:44:18
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
import math

def generate(level=1, **kwargs):
    ops = ['+', '-', '*']
    terms = []
    for _ in range(2):
        a = random.randint(2, 50)
        b = random.randint(2, 50)
        c = random.randint(2, 50)
        d = random.randint(2, 50)
        term = f"({math.isqrt(a)}\\sqrt{{{a}}}"
        if random.random() < 0.5:
            term += f" + {math.isqrt(b)}\\sqrt{{{b}}}"
        else:
            term += f" - {math.isqrt(b)}\\sqrt{{{b}}}"
        term += f")({math.isqrt(c)}\\sqrt{{{c}}}"
        if random.random() < 0.5:
            term += f" + {math.isqrt(d)}\\sqrt{{{d}}})"
        else:
            term += f" - {math.isqrt(d)}\\sqrt{{{d}}})"
        terms.append(term)
    question = f"化簡 ${terms[0]} {random.choice(ops)} {terms[1]}$"
    correct = eval(terms[0].replace('sqrt', 'math.sqrt').replace('(', '').replace(')', '')) 
    correct += eval(terms[1].replace('sqrt', 'math.sqrt').replace('(', '').replace(')', '')) 
    if random.random() < 0.3:
        correct = f"{correct:.2f}"
    else:
        correct = f"{correct:.2f}"
    return {
        'question_text': question,
        'answer': '',
        'correct_answer': correct,
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}