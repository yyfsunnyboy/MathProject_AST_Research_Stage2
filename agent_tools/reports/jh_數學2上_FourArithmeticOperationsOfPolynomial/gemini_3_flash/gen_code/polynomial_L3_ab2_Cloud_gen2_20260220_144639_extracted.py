import random

def generate(level=1, **kwargs):
    var = random.choice(['x', 'a', 'b'])

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
        a_latex = PolynomialOps.format_latex(coeffs_a, var)
        b_latex = PolynomialOps.format_latex(coeffs_b, var)
        question_text = f'計算 $({a_latex}) {op} ({b_latex})$。'
        correct_answer = PolynomialOps.format_plain(result_coeffs, var)

    elif level == 2:
        deg_a = random.randint(1, 2)
        deg_b = random.randint(1, 2)
        coeffs_a = PolynomialOps.random_poly(deg_a)
        coeffs_b = PolynomialOps.random_poly(deg_b)
        result_coeffs = PolynomialOps.mul(coeffs_a, coeffs_b)
        a_latex = PolynomialOps.format_latex(coeffs_a, var)
        b_latex = PolynomialOps.format_latex(coeffs_b, var)
        question_text = f'展開並化簡 $({a_latex})({b_latex})$。'
        correct_answer = PolynomialOps.format_plain(result_coeffs, var)

    else:
        deg_a = random.randint(1, 2)
        deg_b = random.randint(2, 3)
        coeffs_a = PolynomialOps.random_poly(deg_a)
        coeffs_b = PolynomialOps.random_poly(deg_b)
        a_latex = PolynomialOps.format_latex(coeffs_a, var)
        b_latex = PolynomialOps.format_latex(coeffs_b, var)
        choice = random.choice(['A+P=B', 'P-A=B', 'A-P=B'])
        if choice == 'A+P=B':
            result_coeffs = PolynomialOps.sub(coeffs_b, coeffs_a)
            question_text = f'若 $({a_latex}) + P = {b_latex}$，求多項式 $P$。'
        elif choice == 'P-A=B':
            result_coeffs = PolynomialOps.add(coeffs_b, coeffs_a)
            question_text = f'若 $P - ({a_latex}) = {b_latex}$，求多項式 $P$。'
        else:
            result_coeffs = PolynomialOps.sub(coeffs_a, coeffs_b)
            question_text = f'若 $({a_latex}) - P = {b_latex}$，求多項式 $P$。'
        correct_answer = PolynomialOps.format_plain(result_coeffs, var)

    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip().replace(' ', '') == str(correct_answer).strip().replace(' ', '')
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}