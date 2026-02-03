# ==============================================================================
# ID: gh_ApplicationsOfDerivatives
# Model: qwen2.5-coder:14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 13.18s | Tokens: In=606, Out=445
# Created At: 2026-02-03 16:03:26
# Fix Status: [Basic Cleanup] | Fixes: Basic=1, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = FAILED
# ==============================================================================
import random

def generate(level=1, **kwargs):
    # 生成隨機係數和次方
    degree = random.randint(3, 5)  # 隨機選擇多項式的次方，範圍為3到5
    coefficients = [random.randint(-10, 10) for _ in range(degree + 1)]
    
    # 創建多項式函數 f(x)
    def polynomial(x):
        return sum(coeff * x**i for i, coeff in enumerate(reversed(coefficients)))
    
    # 計算一階、二階和三階導數
    from sympy import symbols, diff
    
    x = symbols('x')
    f_x = sum(coeff * x**i for i, coeff in enumerate(reversed(coefficients)))
    f_prime = diff(f_x, x)
    f_double_prime = diff(f_prime, x)
    f_triple_prime = diff(f_double_prime, x)
    
    # 生成題目文字
    question_text = f"已知 $f(x) = {f_x}$，求 $f'(x)$ 與 $f'''(x)$。"
    
    # 正確答案
    correct_answer = f"$f'(x) = {f_prime}$\n$f'''(x) = {f_triple_prime}$"
    
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': str(correct_answer),
        'mode': 1
    }

def check(user_answer, correct_answer):
    # 檢查用戶答案是否正確
    user_answers = user_answer.split('\n')
    correct_answers = correct_answer.split('\n')
    
    if len(user_answers) != len(correct_answers):
        return {'correct': False, 'result': '錯誤'}
    
    for u, c in zip(user_answers, correct_answers):
        if not (u.strip() == c.strip()):
            return {'correct': False, 'result': '錯誤'}
    
    return {'correct': True, 'result': '正確'}