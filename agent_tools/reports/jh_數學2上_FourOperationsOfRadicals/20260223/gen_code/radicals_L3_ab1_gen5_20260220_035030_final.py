# ==============================================================================
# ID: jh_數學2上_FourOperationsOfRadicals
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 34.26s | Tokens: In=753, Out=997
# Created At: 2026-02-20 03:50:30
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
import math

def generate(level=1, **kwargs):
    ops = ['+', '-', '*']
    terms = []
    radicals = [2,3,5,7,11,13,17,19]
    
    if level == 1:
        for _ in range(3):
            a = random.choice(radicals)
            b = random.randint(1,3)
            terms.append(f"{b}\\sqrt{{{a}}}")
        expr = " + ".join(terms)
    else:
        part1 = []
        for _ in range(2):
            a = random.choice(radicals)
            b = random.randint(1,3)
            part1.append(f"{b}\\sqrt{{{a}}}")
        part1 = " + ".join(part1)
        
        part2 = []
        for _ in range(2):
            a = random.choice(radicals)
            b = random.randint(1,3)
            part2.append(f"{b}\\sqrt{{{a}}}")
        part2 = " + ".join(part2)
        
        expr = f"({part1}) + ({part2})({random.choice(ops)} {random.choice(radicals)})"
    
    return {
        'question_text': f"化簡 ${expr}$",
        'answer': '',
        'correct_answer': f"\\sqrt{{{random.randint(2,20)}}}",
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}