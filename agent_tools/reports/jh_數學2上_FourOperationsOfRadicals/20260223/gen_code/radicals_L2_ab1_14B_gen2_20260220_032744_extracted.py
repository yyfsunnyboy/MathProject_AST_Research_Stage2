import random
import math

def generate(level=1, **kwargs):
    ops = ['+', '-', '*', '/']
    terms = []
    for _ in range(2 if level == 1 else 3):
        a = random.randint(2, 20)
        b = random.randint(2, 20)
        c = random.randint(2, 20)
        d = random.randint(2, 20)
        term = f"\\sqrt{{{a}}}"
        if random.random() < 0.4:
            term = f"\\sqrt{{{a}}} + \\sqrt{{{b}}} - \\sqrt{{{c}}}"
        if random.random() < 0.3:
            term = f"(\\sqrt{{{a}}} + \\sqrt{{{b}}})(\\sqrt{{{c}}} - \\sqrt{{{d}}})"
        terms.append(term)
    expr = " + ".join(terms)
    expr = expr.replace(" + ", " + ").replace(" - ", " - ")
    correct_answer = ""
    if random.random() < 0.5:
        correct_answer = f"{random.randint(1, 5)}\\sqrt{{{random.randint(2, 10)}}}"
    else:
        correct_answer = f"-\\sqrt{{{random.randint(2, 10)}}} + \\sqrt{{{random.randint(2, 10)}}}"
    return {
        'question_text': f"化簡 ${expr}$",
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}