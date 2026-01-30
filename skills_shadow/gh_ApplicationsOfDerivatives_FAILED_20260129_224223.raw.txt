import random

def generate(level=1, **kwargs):
    # 確保 level 在有效範圍內
    if not (3 <= level <= 5):
        raise ValueError("level 必須在 3 到 5 之間")
    
    degree = level
    
    # 生成係數列表，確保最高次項非零且至少有 3 個非零係數
    while True:
        polynomial_coeffs = [random.randint(-10, 10) for _ in range(degree + 1)]
        if polynomial_coeffs[degree] != 0 and sum(1 for c in polynomial_coeffs if c != 0) >= 3:
            break
    
    # 確保 derivative_order_1 和 derivative_order_2 在有效範圍內且不同
    while True:
        derivative_order_1 = random.randint(1, degree)
        derivative_order_2 = random.randint(1, degree)
        if derivative_order_1 != derivative_order_2:
            break
    
    # 計算導數係數
    current_coeffs = polynomial_coeffs[:]
    f_prime1_coeffs = None
    f_prime2_coeffs = None
    
    for i in range(1, max(derivative_order_1, derivative_order_2) + 1):
        next_coeffs = [current_coeffs[j] * j for j in range(1, len(current_coeffs))]
        if i == derivative_order_1:
            f_prime1_coeffs = next_coeffs
        if i == derivative_order_2:
            f_prime2_coeffs = next_coeffs
        current_coeffs = next_coeffs
    
    # 驗證導數係數的絕對值是否在範圍內
    for coeff in f_prime1_coeffs + f_prime2_coeffs:
        if abs(coeff) > 1000:
            raise ValueError("導數係數超出範圍")
    
    # 格式化多項式和導數符號
    def fmt_polynomial(coeffs):
        terms = []
        for i, coeff in enumerate(reversed(coeffs)):
            if coeff == 0:
                continue
            term = ""
            if coeff != 1 or i == 0:
                term += str(coeff)
            if i > 0:
                term += "x"
                if i > 1:
                    term += f"^{i}"
            terms.append(term)
        return " + ".join(terms) if terms else "0"
    
    def derivative_symbol(order):
        if order == 1:
            return "f'(x)"
        elif order == 2:
            return "f''(x)"
        else:
            return f"f^{({order})}(x)"
    
    # 組建題目和答案
    f_x_latex = fmt_polynomial(polynomial_coeffs)
    prime1_symbol = derivative_symbol(derivative_order_1)
    prime2_symbol = derivative_symbol(derivative_order_2)
    
    q_str = f"已知 $f(x) = {f_x_latex}$，求 ${prime1_symbol}$ 與 ${prime2_symbol}$。"
    question_output = clean_latex_output(q_str)
    
    ans_prime1 = fmt_polynomial(f_prime1_coeffs)
    ans_prime2 = fmt_polynomial(f_prime2_coeffs)
    answer_output = f"{prime1_symbol} = {ans_prime1}\n{prime2_symbol} = {ans_prime2}"
    
    return {'question_text': question_output, 'answer': answer_output, 'mode': 1}