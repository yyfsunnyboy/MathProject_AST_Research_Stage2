# ==============================================================================
# ID: jh_數學2上_FourOperationsOfRadicals
# Model: Test_Model_Fix | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 23.56s | Tokens: In=753, Out=977
# Created At: 2026-02-20 08:50:09
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
import math

def generate(level=1, **kwargs):
    ops = ['+', '-', '*', '/']
    terms = []
    
    for _ in range(2):
        a = random.randint(1, 10)
        b = random.randint(1, 10)
        c = random.randint(1, 10)
        d = random.randint(1, 10)
        op1 = random.choice(ops)
        op2 = random.choice(ops)
        
        if level == 1:
            term = f"\\sqrt{{{a}}}{op1}\\sqrt{{{b}}} {op2} \\sqrt{{{c}}}{op1}\\sqrt{{{d}}}"
        else:
            term = f"({random.choice(['\\sqrt', '\\sqrt[3]'])}{{{a}}}{op1}{random.choice(['\\sqrt', '\\sqrt[3]'])}{{{b}}}) {op2} ({random.choice(['\\sqrt', '\\sqrt[3]'])}{{{c}}}{op1}{random.choice(['\\sqrt', '\\sqrt[3]'])}{{{d}}})"
        
        terms.append(term)
    
    question = f"化簡 ${{{terms[0]}}}$"
    correct = simplify(f"{terms[0]}")
    
    return {
        'question_text': question,
        'answer': '',
        'correct_answer': correct,
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}

def simplify(expr):
    expr = expr.replace('sqrt', 'math.sqrt').replace('sqrt[3]', 'math.sqrt[3]')
    return eval(expr)