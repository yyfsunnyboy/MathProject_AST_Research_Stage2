import random
import math

def generate(level=1, **kwargs):
    question_text = ""
    answer = ""
    correct_answer = ""
    mode = 1
    operations = ['+', '-']
    radicals = [random.randint(2, 20) for _ in range(4)]
    coefficients = [random.randint(1, 5) for _ in range(4)]
    terms = []
    for i in range(2):
        term = f"{coefficients[i]}\\sqrt{{{radicals[i]}}}"
        terms.append(term)
    part1 = " + ".join(terms)
    part2 = f"({terms[2]}{random.choice(operations)}{terms[3]})"
    question_text = f"化簡 $({part1}) + ({part2})$"
    correct_answer = f"{sum(coefficients[:2])}\\sqrt{{{radicals[0]}}} + {sum(coefficients[2:])}\\sqrt{{{radicals[2]}}} + {coefficients[2] * coefficients[3]}\\sqrt{{{radicals[2] * radicals[3]}}}"
    return {'question_text': question_text, 'answer': answer, 'correct_answer': correct_answer, 'mode': mode}

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}