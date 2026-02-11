# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: qwen2.5-coder-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 10.71s | Tokens: In=617, Out=306
# Created At: 2026-02-09 09:41:55
# Fix Status: [Basic Cleanup Only] | Fixes: Basic=1, Advanced=None
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
    
    def random_expression(depth=0):
        if depth == 3 or random.random() < 0.5:
            num = random_number()
            if random.random() < 0.2 and level > 1:
                return f"abs({num})"
            else:
                return str(num)
        
        left = random_expression(depth + 1)
        op = random_operator()
        right = random_expression(depth + 1)
        
        if op == '/' and int(right) == 0:
            right = '1'
        
        expression = f"({left}{op}{right})"
        return expression
    
    question_text = random_expression()
    correct_answer = str(eval(question_text))
    
    return {
        'question_text': f'計算 {question_text} 的值。',
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