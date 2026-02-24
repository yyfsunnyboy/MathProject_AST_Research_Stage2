import random
import math

def generate(level=1, **kwargs):
    question = []
    terms = []
    operations = ['+', '-']
    num_terms = random.randint(2, 4)
    for _ in range(num_terms):
        sign = random.choice(operations)
        coefficient = random.randint(1, 5)
        radicand = random.randint(2, 100)
        sqrt = math.sqrt(radicand)
        if sqrt.is_integer():
            radicand = int(sqrt ** 2)
        terms.append(f"{coefficient}\\sqrt{{{radicand}}}")
    question.append(" + ".join(terms))
    terms2 = []
    for _ in range(2):
        coefficient = random.randint(1, 5)
        radicand = random.randint(2, 100)
        sqrt = math.sqrt(radicand)
        if sqrt.is_integer():
            radicand = int(sqrt ** 2)
        terms2.append(f"{coefficient}\\sqrt{{{radicand}}}")
    question.append(f"({terms2[0]} + {terms2[1]})(\\sqrt{{{random.randint(2, 100)}}} - {random.randint(1, 5)})")
    question_text = f"化簡 $({' + '.join(question)})$"
    answer = ""
    correct_answer = f"{random.randint(1, 10)}\\sqrt{{{random.randint(2, 100)}}}"
    return {
        'question_text': question_text,
        'answer': answer,
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}