# ==============================================================================
# ID: gh_ApplicationsOfDerivatives
# Model: qwen2.5-coder:14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 18.18s | Tokens: In=606, Out=582
# Created At: 2026-02-02 23:52:58
# Fix Status: [Basic Cleanup] | Fixes: Basic=1, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PASSED
# ==============================================================================
import random

def generate(level=1, **kwargs):
    # 生成一個隨機的多項式函數
    degree = random.randint(3, 5)  # 隨機選擇多項式的次方，範圍在3到5之間
    coefficients = [random.randint(-10, 10) for _ in range(degree + 1)]  # 生成隨機係數
    
    # 創建函數 f(x)
    def create_function(coefficients):
        terms = []
        for i, coeff in enumerate(reversed(coefficients)):
            if coeff != 0:
                term = f"{coeff}x^{len(coefficients) - i - 1}" if len(coefficients) - i - 1 > 1 else "x" if len(coefficients) - i - 1 == 1 else str(coeff)
                terms.append(term)
        return " + ".join(terms)
    
    f_x = create_function(coefficients)
    
    # 計算一階導數 f'(x)
    def first_derivative(coefficients):
        derivative_coeffs = [coeff * (len(coefficients) - i - 1) for i, coeff in enumerate(reversed(coefficients))][:-1]
        return create_function(derivative_coeffs)
    
    f_prime_x = first_derivative(coefficients)
    
    # 計算三階導數 f'''(x)
    def third_derivative(coefficients):
        derivative_coeffs = [coeff * (len(coefficients) - i - 1) for i, coeff in enumerate(reversed(coefficients))][:-3]
        return create_function(derivative_coeffs)
    
    f_triple_prime_x = third_derivative(coefficients)
    
    # 創建題目文字
    question_text = f"已知 $f(x) = {f_x}$，求 $f'(x)$ 與 $f'''(x)$。"
    
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': f"{f_prime_x}, {f_triple_prime_x}",
        'mode': 1
    }

def check(user_answer, correct_answer):
    user_answers = [ans.strip() for ans in user_answer.split(',')]
    correct_answers = [ans.strip() for ans in correct_answer.split(',')]
    
    # 檢查用戶答案是否正確
    if len(user_answers) != len(correct_answers):
        return {'correct': False, 'result': '錯誤'}
    
    for ua, ca in zip(sorted(user_answers), sorted(correct_answers)):
        if ua != ca:
            return {'correct': False, 'result': '錯誤'}
    
    return {'correct': True, 'result': '正確'}