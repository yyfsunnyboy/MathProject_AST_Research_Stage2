# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: qwen2.5-coder-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 15.40s | Tokens: In=617, Out=444
# Created At: 2026-02-09 09:41:44
# Fix Status: [Basic Cleanup Only] | Fixes: Basic=1, Advanced=None
# Verification: Internal Logic Check = FAILED
# ==============================================================================

import random

def generate(level=1, **kwargs):
    def random_int():
        return random.randint(-20, 20)
    
    def random_operator():
        return random.choice(['+', '-', '*', '÷'])
    
    def random_expression(depth=0):
        if depth == 0:
            op = random.choice(['+', '-'])
            left = f"({random_expression(1)})"
            right = f"({random_expression(1)})"
            return f"{left}{op}{right}"
        
        elif depth == 1:
            num1, num2 = random_int(), random_int()
            if level > 1 and random.random() < 0.5:
                op = random.choice(['+', '-'])
                expr = f"({random_expression(2)})"
                return f"{expr}{op}{num1}"
            
            elif level > 2 and random.random() < 0.3:
                abs_expr = f"|{random_int()}×{random_int()}-{random_int()}|"
                op = random.choice(['+', '-'])
                return f"{abs_expr}{op}{num1}"
            
            else:
                return f"{num1} {random_operator()} {num2}"
        
        elif depth == 2:
            num = random_int()
            if level > 3 and random.random() < 0.5:
                op = random.choice(['+', '-'])
                expr = f"({random_expression(3)})"
                return f"{expr}{op}{num}"
            
            else:
                return str(num)
    
    question_text = f"計算 {random_expression()} 的值。"
    correct_answer = str(eval(question_text.replace('÷', '/')))
    
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    user_answer = user_answer.strip()
    if user_answer == correct_answer:
        return {'correct': True, 'result': '正確'}
    else:
        return {'correct': False, 'result': '錯誤'}