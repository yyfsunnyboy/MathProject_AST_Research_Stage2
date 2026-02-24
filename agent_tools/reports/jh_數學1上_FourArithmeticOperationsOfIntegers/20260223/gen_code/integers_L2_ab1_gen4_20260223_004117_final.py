# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 52.74s | Tokens: In=624, Out=1353
# Created At: 2026-02-23 00:41:17
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random

def generate(level=1, **kwargs):
    ops = ['+', '-', '÷', '×']
    num_range = [(-50, 50), (-100, 100)][level-1]
    a = random.randint(*num_range)
    b = random.randint(*num_range)
    c = random.randint(*num_range)
    d = random.randint(*num_range)
    e = random.randint(*num_range)
    f = random.randint(*num_range)
    
    part1 = f"({a}{ops[0]}{b})"
    part2 = f"{c}{ops[1]}{d}"
    part3 = f"{e}{ops[2]}{f}"
    
    question = f"{part1}{ops[3]}{part2}×{part3}+|{part3}|"
    question = question.replace('÷', '/').replace('×', '*')
    
    try:
        correct_answer = eval(question)
        if not isinstance(correct_answer, int):
            raise ValueError
    except:
        return generate(level, **kwargs)
    
    return {
        'question_text': question.replace('/', '÷').replace('*', '×'),
        'answer': '',
        'correct_answer': str(int(correct_answer)),
        'mode': 1
    }

def check(user_answer, correct_answer):
    return {
        'correct': user_answer == correct_answer,
        'result': '正確' if user_answer == correct_answer else '錯誤'
    }