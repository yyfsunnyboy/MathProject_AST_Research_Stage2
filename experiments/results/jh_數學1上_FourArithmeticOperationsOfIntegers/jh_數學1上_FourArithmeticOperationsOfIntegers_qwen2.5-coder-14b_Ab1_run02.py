# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: qwen2.5-coder-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 11.93s | Tokens: In=617, Out=343
# Created At: 2026-02-09 09:41:16
# Fix Status: [Basic Cleanup Only] | Fixes: Basic=1, Advanced=None
# Verification: Internal Logic Check = FAILED
# ==============================================================================

import random

def generate(level=1, **kwargs):
    def random_operator():
        return random.choice(['+', '-', '*', '÷'])
    
    def random_number(min_val=-20, max_val=20):
        return random.randint(min_val, max_val)
    
    def create_expression(depth=3):
        if depth == 0:
            return str(random_number())
        
        operator = random_operator()
        left_expr = create_expression(depth - 1)
        right_expr = create_expression(depth - 1)
        
        if operator == '÷':
            while int(right_expr) == 0:
                right_expr = create_expression(depth - 1)
        
        return f"({left_expr}{operator}{right_expr})"
    
    def add_absolute_value(expression):
        if random.choice([True, False]):
            return f"|{expression}|"
        return expression
    
    depth = random.randint(2, level + 2)
    base_expr = create_expression(depth)
    expr_with_abs = add_absolute_value(base_expr)
    
    question_text = f"計算 {expr_with_abs} 的值。"
    correct_answer = str(eval(expr_with_abs.replace('÷', '/')))
    
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    user_answer = user_answer.strip()
    correct_answer = str(correct_answer)
    
    if user_answer == correct_answer:
        return {'correct': True, 'result': '正確'}
    else:
        return {'correct': False, 'result': '錯誤'}