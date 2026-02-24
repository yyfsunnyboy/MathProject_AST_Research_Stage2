# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 54.13s | Tokens: In=624, Out=1382
# Created At: 2026-02-23 00:38:18
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random

def generate(level=1, **kwargs):
    ops = ['+', '-', '÷', '×']
    abs_pos = random.randint(0, 2)
    nums = [random.randint(-20, 20) for _ in range(7)]
    while nums[2] == 0 or nums[5] == 0:
        nums = [random.randint(-20, 20) for _ in range(7)]
    
    if abs_pos == 0:
        expr = f"|{nums[0]}{ops[0]}{nums[1]}|{ops[3]}{nums[2]}{ops[1]}{nums[3]}{ops[2]}{nums[4]}{ops[3]}{nums[5]}{ops[1]}{nums[6]}"
    elif abs_pos == 1:
        expr = f"({nums[0]}{ops[0]}{nums[1]}){ops[3]}{nums[2]}{ops[1]}|{nums[3]}{ops[0]}{nums[4]}|{ops[2]}{nums[5]}{ops[1]}{nums[6]}"
    else:
        expr = f"({nums[0]}{ops[0]}{nums[1]}){ops[3]}{nums[2]}{ops[1]}{nums[3]}{ops[2]}{nums[4]}{ops[3]}|{nums[5]}{ops[0]}{nums[6]}|"
    
    expr = expr.replace('÷', '/').replace('×', '*')
    correct_answer = str(int(eval(expr)))
    return {
        'question_text': expr.replace('/', '÷').replace('*', '×'),
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        return {
            'correct': user_answer.strip() == correct_answer,
            'result': '正確' if user_answer.strip() == correct_answer else '錯誤'
        }
    except:
        return {
            'correct': False,
            'result': '錯誤'
        }