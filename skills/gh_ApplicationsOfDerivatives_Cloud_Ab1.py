# ==============================================================================
# ID: gh_ApplicationsOfDerivatives
# Model: gemini-2.5-flash | Strategy: V47.5 Unified-Cleanup + Advanced-Healer
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 35.18s | Tokens: In=369, Out=2077
# Created At: 2026-01-31 16:20:56
# Fix Status: [Basic Cleanup] | Fixes: Basic=2, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PASSED
# ==============================================================================
import random

def _format_polynomial(coeffs, var='x'):
    """
    Formats a list of polynomial coefficients into a string.
    Input: coeffs as [a_n, a_{n-1}, ..., a_0] for a_n*x^n + ... + a_0
    Output: A string representing the polynomial, e.g., "3x^3 - 2x^2 + 5"
    """
    if not coeffs:
        return "0"

    terms = []
    degree = len(coeffs) - 1

    for i, coeff in enumerate(coeffs):
        current_degree = degree - i

        if coeff == 0:
            continue

        # Determine sign
        sign = "+" if coeff > 0 else "-"
        abs_coeff = abs(coeff)

        # Handle first term sign
        if not terms and sign == "+":
            sign = "" # No '+' for the very first term if positive

        term_str = ""
        if current_degree == 0: # Constant term
            term_str = f"{abs_coeff}"
        elif current_degree == 1: # x term
            if abs_coeff == 1:
                term_str = f"{var}"
            else:
                term_str = f"{abs_coeff}{var}"
        else: # x^n term (n > 1)
            if abs_coeff == 1:
                term_str = f"{var}^{current_degree}"
            else:
                term_str = f"{abs_coeff}{var}^{current_degree}"

        terms.append(f"{sign}{term_str}")

    if not terms:
        return "0" # All coeffs were zero

    return "".join(terms)

def _derive_polynomial_coeffs(coeffs):
    """
    Calculates the coefficients of the derivative of a polynomial.
    Input: [a_n, a_{n-1}, ..., a_0]
    Output: [n*a_n, (n-1)*a_{n-1}, ..., 1*a_1]
    """
    if len(coeffs) <= 1: # Constant or empty polynomial
        return [0] # Derivative of a constant is 0

    derived_coeffs = []
    degree = len(coeffs) - 1
    for i in range(degree): # Iterate from n down to 1
        derived_coeffs.append(coeffs[i] * (degree - i))

    if not derived_coeffs: # This case should ideally not happen if input is not [0] and not a constant
        return [0]
    return derived_coeffs

def generate(level=1, **kwargs):
    """
    生成導數應用相關的數學題目。

    Args:
        level (int): 題目的難度等級。
                     level 1: 求 f'(x)
                     level 2: 求 f'(x) 與 f''(x)
        **kwargs: 額外參數，目前未使用。

    Returns:
        dict: 包含題目文字、答案及模式的字典。
    """
    # 根據難度等級隨機決定多項式的最高次數
    if level == 1:
        degree = random.randint(3, 4) # 3次或4次多項式
    elif level == 2:
        degree = random.randint(4, 5) # 4次或5次多項式
    else: # 預設為 level 1
        degree = random.randint(3, 4)

    # 生成多項式的係數
    coeffs = []
    # 確保首項係數不為零
    coeffs.append(random.choice([c for c in range(-5, 6) if c != 0]))
    # 其他項係數可以為零
    for _ in range(degree):
        coeffs.append(random.randint(-5, 5))

    # 格式化原始函數 f(x)
    f_x_str = _format_polynomial(coeffs)

    # 計算 f'(x) 的係數並格式化
    f_prime_coeffs = _derive_polynomial_coeffs(coeffs)
    f_prime_x_str = _format_polynomial(f_prime_coeffs)

    question_text = ""
    answer_text = ""
    
    if level == 1:
        question_text = f"已知 $f(x) = {f_x_str}$，求 $f'(x)$。"
        answer_text = f"$f'(x) = {f_prime_x_str}$"
    elif level == 2:
        # 計算 f''(x) 的係數並格式化
        f_double_prime_coeffs = _derive_polynomial_coeffs(f_prime_coeffs)
        f_double_prime_x_str = _format_polynomial(f_double_prime_coeffs)

        question_text = f"已知 $f(x) = {f_x_str}$，求 $f'(x)$ 與 $f''(x)$。"
        answer_text = f"$f'(x) = {f_prime_x_str}$\n$f''(x) = {f_double_prime_x_str}$"
    else: # 其他 level 預設為 level 1
        question_text = f"已知 $f(x) = {f_x_str}$，求 $f'(x)$。"
        answer_text = f"$f'(x) = {f_prime_x_str}$"

    return {
        'question_text': question_text,
        'answer': answer_text,
        'correct_answer': answer_text,
        'mode': 1
    }

def check(user_answer, correct_answer):
    """
    檢查使用者答案是否正確。

    Args:
        user_answer (str): 使用者提交的答案字串。
        correct_answer (str): 正確答案字串。

    Returns:
        dict: 包含 'correct' (布林值) 和 'result' (字串) 的字典。
    """
    # 將答案字串按行分割並去除每行前後的空白，以便進行精確比較
    user_lines = [line.strip() for line in user_answer.strip().split('\n')]
    correct_lines = [line.strip() for line in correct_answer.strip().split('\n')]

    is_correct = (user_lines == correct_lines)

    return {
        'correct': is_correct,
        'result': '正確' if is_correct else '錯誤'
    }

# 範例使用 (此部分不會在最終輸出中，僅供測試參考)
if __name__ == '__main__':
    print("--- Level 1 題目範例 ---")
    problem1 = generate(level=1)
    print("題目:", problem1['question_text'])
    print("正確答案:", problem1['correct_answer'])
    
    # 測試正確答案
    user_ans1_correct = problem1['correct_answer']
    check_result1_correct = check(user_ans1_correct, problem1['correct_answer'])
    print(f"使用者答案 (正確): \"{user_ans1_correct}\" -> {check_result1_correct['result']}")

    # 測試錯誤答案 (故意修改)
    user_ans1_wrong = problem1['correct_answer'].replace('x^', 'y^') # 替換變數
    check_result1_wrong = check(user_ans1_wrong, problem1['correct_answer'])
    print(f"使用者答案 (錯誤): \"{user_ans1_wrong}\" -> {check_result1_wrong['result']}")

    print("\n--- Level 2 題目範例 ---")
    problem2 = generate(level=2)
    print("題目:", problem2['question_text'])
    print("正確答案:\n", problem2['correct_answer'])

    # 測試正確答案
    user_ans2_correct = problem2['correct_answer']
    check_result2_correct = check(user_ans2_correct, problem2['correct_answer'])
    print(f"使用者答案 (正確):\n\"{user_ans2_correct}\"\n-> {check_result2_correct['result']}")

    # 測試錯誤答案 (少一行)
    user_ans2_wrong = problem2['correct_answer'].split('\n')[0] # 只取f'(x)
    check_result2_wrong = check(user_ans2_wrong, problem2['correct_answer'])
    print(f"使用者答案 (錯誤):\n\"{user_ans2_wrong}\"\n-> {check_result2_wrong['result']}")

    print("\n--- 再次生成 Level 1 題目 (確認隨機性) ---")
    problem3 = generate(level=1)
    print("題目:", problem3['question_text'])
    print("正確答案:", problem3['correct_answer'])