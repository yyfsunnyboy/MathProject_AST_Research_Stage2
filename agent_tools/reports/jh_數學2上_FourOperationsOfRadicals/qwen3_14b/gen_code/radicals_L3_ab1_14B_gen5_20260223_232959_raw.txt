import random
import math

def generate(level=1, **kwargs):
    question = ""
    answer = ""
    correct_answer = ""
    mode = 1
    operations = ['+', '-', '*', '/']
    num_terms = random.randint(2, 4)
    terms = []
    for _ in range(num_terms):
        sign = random.choice(operations)
        if sign == '+':
            terms.append(f"{random.randint(1, 5)}\\sqrt{{{random.randint(2, 10)}}}")
        elif sign == '-':
            terms.append(f"-{random.randint(1, 5)}\\sqrt{{{random.randint(2, 10)}}}")
        elif sign == '*':
            a = random.randint(1, 5)
            b = random.randint(2, 10)
            c = random.randint(1, 5)
            d = random.randint(2, 10)
            terms.append(f"({a}\\sqrt{{{b}}})({c}\\sqrt{{{d}}})")
        else:
            a = random.randint(1, 5)
            b = random.randint(2, 10)
            c = random.randint(1, 5)
            d = random.randint(2, 10)
            terms.append(f"\\frac{{{a}\\sqrt{{{b}}}}}{{{c}\\sqrt{{{d}}}}}")
    question = " + ".join(terms)
    answer = ""
    correct_answer = question
    return {'question_text': f"化簡 ${question}$", 'answer': answer, 'correct_answer': correct_answer, 'mode': mode}

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}