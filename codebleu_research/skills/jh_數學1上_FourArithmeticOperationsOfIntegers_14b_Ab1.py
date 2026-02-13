# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: qwen2.5-coder:14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 15.62s | Tokens: In=617, Out=379
# Created At: 2026-02-08 21:43:54
# Fix Status: [Basic Cleanup] | Fixes: Basic=1, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PASSED
# ==============================================================================
import random

def generate(level=1, **kwargs):
    def random_number():
        return random.randint(-20, 20)
    
    def random_operator():
        operators = ['+', '-', '*', '/']
        if level > 1:
            operators.append('**')
        return random.choice(operators)
    
    def create_expression(depth=1):
        if depth == 0 or random.random() < 0.3:
            num = random_number()
            if num < 0:
                return f"({num})"
            else:
                return str(num)
        
        left_expr = create_expression(depth - 1)
        operator = random_operator()
        right_expr = create_expression(depth - 1)
        
        if operator == '/':
            while int(right_expr) == 0:
                right_expr = create_expression(depth - 1)
        
        expr = f"{left_expr}{operator}{right_expr}"
        if random.random() < 0.5 and depth > 1:
            return f"({expr})"
        else:
            return expr
    
    def add_absolute_value(expr):
        if random.random() < 0.3:
            return f"|{expr}|"
        return expr
    
    expression = create_expression(2)
    expression = add_absolute_value(expression)
    
    question_text = f"計算 {expression} 的值。"
    correct_answer = str(eval(expression))
    
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