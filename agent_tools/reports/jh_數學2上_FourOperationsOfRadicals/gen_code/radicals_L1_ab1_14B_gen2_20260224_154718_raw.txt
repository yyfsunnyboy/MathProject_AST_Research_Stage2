import random
import math

def generate(level=1, **kwargs):
    ops = ['+', '-', '*', '/']
    terms = []
    for _ in range(3):
        if random.random() < 0.5:
            coeff = random.randint(1, 10)
            radicand = random.randint(2, 50)
            terms.append(f"{coeff}\\sqrt{{{radicand}}}")
        else:
            coeff = random.randint(1, 10)
            radicand = random.randint(2, 50)
            terms.append(f"-{coeff}\\sqrt{{{radicand}}}")
    expr1 = " + ".join(terms)
    terms2 = []
    for _ in range(2):
        if random.random() < 0.5:
            coeff = random.randint(1, 10)
            radicand = random.randint(2, 50)
            terms2.append(f"{coeff}\\sqrt{{{radicand}}}")
        else:
            coeff = random.randint(1, 10)
            radicand = random.randint(2, 50)
            terms2.append(f"-{coeff}\\sqrt{{{radicand}}}")
    expr2 = " + ".join(terms2)
    question_text = f"化簡 $({expr1}) + ({expr2})$"
    answer = ""
    correct_answer = ""
    mode = 1
    return {'question_text': question_text, 'answer': answer, 'correct_answer': correct_answer, 'mode': mode}

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}