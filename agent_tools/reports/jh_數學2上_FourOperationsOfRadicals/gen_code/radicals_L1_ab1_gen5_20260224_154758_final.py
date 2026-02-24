# ==============================================================================
# ID: jh_數學2上_FourOperationsOfRadicals
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 9.50s | Tokens: In=759, Out=398
# Created At: 2026-02-24 15:47:58
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
import math

def generate(level=1, **kwargs):
    question_text = ''
    answer = ''
    correct_answer = ''
    mode = 1
    
    if level == 1:
        a = random.randint(2, 10)
        b = random.randint(2, 10)
        c = random.randint(2, 10)
        d = random.randint(2, 10)
        e = random.randint(2, 10)
        f = random.randint(2, 10)
        op1 = random.choice(['+', '-'])
        op2 = random.choice(['+', '-'])
        op3 = random.choice(['+', '-'])
        op4 = random.choice(['+', '-'])
        op5 = random.choice(['+', '-'])
        op6 = random.choice(['+', '-'])
        
        term1 = f"{a}\\sqrt{{{b}}}"
        term2 = f"{c}\\sqrt{{{d}}}"
        term3 = f"{e}\\sqrt{{{f}}}"
        term4 = f"{a}\\sqrt{{{b}}}"
        term5 = f"{c}\\sqrt{{{d}}}"
        term6 = f"{e}\\sqrt{{{f}}}"
        
        question_text = f"化簡 $({term1} {op1} {term2} {op2} {term3}) + ({term4} {op3} {term5} {op4} {term6})$"
        answer = ''
        correct_answer = f"{a + c + e}\\sqrt{{{b}}}"
    
    return {'question_text': question_text, 'answer': answer, 'correct_answer': correct_answer, 'mode': mode}

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}