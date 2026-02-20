import random

def generate(level=1, **kwargs):
    var = random.choice(['x', 'y', 'a', 'b'])
    
    if level == 1:
        deg_a = random.randint(2, 3)
        deg_b = random.randint(2, 3)
        coeffs_a = PolynomialOps.random_poly(deg_a)
        coeffs_b = PolynomialOps.random_poly(deg_b)
        op = random.choice(['+', '-'])
        if op == '+':
            result_coeffs = PolynomialOps.add(coeffs_a, coeffs_b)
        else:
            result_coeffs = PolynomialOps.sub(coeffs_a, coeffs_b)
        a_str = PolynomialOps.format_latex(coeffs_a, var)
        b_str = PolynomialOps.format_latex(coeffs_b, var)
        question_text = f"計算 $({a_str}) {op} ({b_str})$。"
        correct_answer = PolynomialOps.format_plain(result_coeffs, var)
        
    elif level == 2:
        coeffs_a = PolynomialOps.random_poly(1)
        coeffs_b = PolynomialOps.random_poly(2)
        result_coeffs = PolynomialOps.mul(coeffs_a, coeffs_b)
        a_str = PolynomialOps.format_latex(coeffs_a, var)
        b_str = PolynomialOps.format_latex(coeffs_b, var)
        question_text = f"展開 $({a_str})({b_str})$。"
        correct_answer = PolynomialOps.format_plain(result_coeffs, var)
        
    else:
        deg_a = random.randint(1, 2)
        deg_b = random.randint(2, 3)
        coeffs_a = PolynomialOps.random_poly(deg_a)
        coeffs_b = PolynomialOps.random_poly(deg_b)
        type_choice = random.choice(['add', 'sub'])
        a_str = PolynomialOps.format_latex(coeffs_a, var)
        b_str = PolynomialOps.format_latex(coeffs_b, var)
        if type_choice == 'add':
            result_coeffs = PolynomialOps.sub(coeffs_b, coeffs_a)
            question_text = f"若 $X + ({a_str}) = {b_str}$，求多項式 $X$。"
        else:
            result_coeffs = PolynomialOps.add(coeffs_b, coeffs_a)
            question_text = f"若 $X - ({a_str}) = {b_str}$，求多項式 $X$。"
        correct_answer = PolynomialOps.format_plain(result_coeffs, var)
    
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}