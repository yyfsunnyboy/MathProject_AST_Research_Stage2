# ==============================================================================
# ID: jh_數學2上_FourOperationsOfRadicals
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 34.95s | Tokens: In=753, Out=1019
# Created At: 2026-02-20 03:42:37
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
import math

def generate(level=1, **kwargs):
    ops = ['+', '-', '*']
    a = random.randint(2, 20)
    b = random.randint(2, 20)
    c = random.randint(2, 20)
    d = random.randint(2, 20)
    e = random.randint(2, 20)
    f = random.randint(2, 20)
    g = random.randint(2, 20)
    h = random.randint(2, 20)
    
    part1 = f"\\sqrt{{{a}}} + \\sqrt{{{b}}} - {random.randint(1,3)}\\sqrt{{{c}}}"
    part2 = f"(\\sqrt{{{d}}} + \\sqrt{{{e}}})(\\sqrt{{{f}}} - \\sqrt{{{g}}})"
    
    question = f"{part1} + {part2}"
    correct = f"{math.sqrt(a)+math.sqrt(b)-random.randint(1,3)*math.sqrt(c)} + {math.sqrt(d)*math.sqrt(f) + math.sqrt(e)*math.sqrt(f) - math.sqrt(d)*math.sqrt(g) - math.sqrt(e)*math.sqrt(g)}"
    
    return {
        'question_text': f"化簡 ${question}$",
        'answer': '',
        'correct_answer': f"{correct}",
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}