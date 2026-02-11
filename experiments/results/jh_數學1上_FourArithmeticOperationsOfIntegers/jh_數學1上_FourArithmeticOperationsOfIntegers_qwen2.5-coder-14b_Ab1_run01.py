# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: qwen2.5-coder-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 24.01s | Tokens: In=617, Out=497
# Created At: 2026-02-09 09:41:02
# Fix Status: [Basic Cleanup Only] | Fixes: Basic=1, Advanced=None
# Verification: Internal Logic Check = PASSED
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
        
        # Add parentheses with a certain probability
        if random.random() < 0.5:
            left_expr = f"({left_expr})"
        if random.random() < 0.5:
            right_expr = f"({right_expr})"
        
        return f"{left_expr} {operator} {right_expr}"
    
    def add_absolute_value(expression):
        if random.random() < 0.3:
            return f"|{expression}|"
        return expression
    
    # Generate the main expression
    main_expression = create_expression()
    main_expression = add_absolute_value(main_expression)
    
    # Add more complexity based on level
    for _ in range(level - 1):
        operator = random_operator()
        sub_expr = create_expression()
        sub_expr = add_absolute_value(sub_expr)
        
        if random.random() < 0.5:
            main_expression = f"{main_expression} {operator} {sub_expr}"
        else:
            main_expression = f"{sub_expr} {operator} {main_expression}"
    
    # Replace '÷' with '/' for evaluation
    eval_expression = main_expression.replace('÷', '/')
    
    try:
        correct_answer = str(eval(eval_expression))
    except ZeroDivisionError:
        return generate(level, **kwargs)
    
    question_text = f"計算 {main_expression} 的值。"
    
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    user_answer = str(user_answer).strip()
    correct_answer = str(correct_answer)
    
    if user_answer == correct_answer:
        return {
            'correct': True,
            'result': '正確'
        }
    else:
        return {
            'correct': False,
            'result': '錯誤'
}