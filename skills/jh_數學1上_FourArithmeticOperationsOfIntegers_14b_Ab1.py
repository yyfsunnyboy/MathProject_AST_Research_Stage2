# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: qwen2.5-coder:14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 13.78s | Tokens: In=616, Out=279
# Created At: 2026-02-06 13:26:31
# Fix Status: [Basic Cleanup] | Fixes: Basic=1, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PASSED
# ==============================================================================
import random

def generate(level=1, **kwargs):
    # Generate random integers for the problem
    a = random.randint(-50, 50)
    b = random.randint(-50, 50)
    c = random.randint(-50, 50)
    d = random.randint(1, 50)  # Ensure division by zero is avoided

    # Create the expression
    question_text = f"計算 [ ({a})＋({b}) ]÷({c})×{d} +｜{a}×({b})-{c}｜的值。"
    
    # Calculate the correct answer
    inside_brackets = a + b
    division_multiplication = (inside_brackets / c) * d
    absolute_value = abs(a * b - c)
    correct_answer = str(division_multiplication + absolute_value)

    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    # Check if the user's answer matches the correct answer
    return {
        'correct': str(user_answer) == correct_answer,
        'result': '正確' if str(user_answer) == correct_answer else '錯誤'
    }