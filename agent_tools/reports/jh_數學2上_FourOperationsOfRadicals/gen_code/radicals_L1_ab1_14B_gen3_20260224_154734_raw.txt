import random
import math

def generate(level=1, **kwargs):
    question_text = ''
    answer = ''
    correct_answer = ''
    mode = 1
    operations = ['+', '-', '*', '/']
    num_terms = random.randint(2, 4)
    terms = []
    for _ in range(num_terms):
        coeff = random.randint(1, 5)
        radicand = random.randint(2, 50)
        sqrt = math.sqrt(radicand)
        if sqrt.is_integer():
            radicand = int(sqrt ** 2)
        terms.append(f"{coeff}\\sqrt{{{radicand}}}")
    operation = random.choice(operations)
    if operation == '+':
        question_text = f"化簡 $({' + ').join(terms)}$"
        correct_answer = f"{sum([int(term.split('sqrt')[0]) for term in terms])}\\sqrt{{{radicand}}}"
    elif operation == '-':
        question_text = f"化簡 $({' - ').join(terms)}$"
        correct_answer = f"{sum([int(term.split('sqrt')[0]) for term in terms])}\\sqrt{{{radicand}}}"
    elif operation == '*':
        term1 = random.choice(terms)
        term2 = random.choice(terms)
        question_text = f"化簡 ${term1} \\cdot {term2}$"
        coeff1 = int(term1.split('sqrt')[0])
        radicand1 = int(term1.split('sqrt')[1].split('}')[0])
        coeff2 = int(term2.split('sqrt')[0])
        radicand2 = int(term2.split('sqrt')[1].split('}')[0])
        correct_answer = f"{coeff1 * coeff2}\\sqrt{{{radicand1 * radicand2}}}"
    elif operation == '/':
        term1 = random.choice(terms)
        term2 = random.choice(terms)
        question_text = f"化簡 ${term1} \\div {term2}$"
        coeff1 = int(term1.split('sqrt')[0])
        radicand1 = int(term1.split('sqrt')[1].split('}')[0])
        coeff2 = int(term2.split('sqrt')[0])
        radicand2 = int(term2.split('sqrt')[1].split('}')[0])
        correct_answer = f"\\frac{{{coeff1}}}}{{{coeff2}}}\\sqrt{{{radicand1 / radicand2}}}"
    return {'question_text': question_text, 'answer': answer, 'correct_answer': correct_answer, 'mode': mode}

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}