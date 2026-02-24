import random
import math

radicand_list = [2, 3, 5, 6, 7, 8, 10, 12, 14, 15, 18, 20, 24, 25, 27, 30, 32, 35, 40, 45, 48, 49, 50, 54, 63, 64, 72, 80, 81, 90, 96, 98, 99, 100]

def generate(level=1, **kwargs):
    terms1 = []
    for _ in range(3):
        radicand = random.choice(radicand_list)
        coefficient = random.randint(1, 5)
        terms1.append(f"{coefficient}\\sqrt{{{radicand}}}")
    terms1 = [random.choice(['+', '-']) + term for term in terms1]
    terms1 = [term.replace('+', '') if term.startswith('+') else term for term in terms1]
    terms1 = [term.replace('-', '') if term.startswith('-') else term for term in terms1]
    terms1 = [term for term in terms1 if term != '']
    
    a = random.choice(radicand_list)
    b = random.choice(radicand_list)
    c = random.choice(radicand_list)
    d = random.randint(1, 5)
    binomial1 = f"\\sqrt{{{a}}} + \\sqrt{{{b}}}"
    binomial2 = f"\\sqrt{{{c}}} - {d}"
    question_text = f"({'+'.join(terms1)}) + ({binomial1})({binomial2})"
    
    correct_answer = ""
    return {
        'question_text': f"${question_text}$",
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': 'Correct' if correct else 'Wrong'}