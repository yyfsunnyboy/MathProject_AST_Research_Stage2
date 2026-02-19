import random
import math

def generate(level=1, **kwargs):
    ops = ['+', '-', '*', '/']
    terms = []
    for _ in range(2):
        a = random.randint(1, 20)
        b = random.randint(1, 20)
        c = random.randint(1, 20)
        d = random.randint(1, 20)
        terms.append(f"\\sqrt{{{a}}} + \\sqrt{{{b}}} - \\sqrt{{{c}}}")
        terms.append(f"\\sqrt{{{d}}} + \\sqrt{{{random.randint(1,20)}}} \\cdot \\sqrt{{{random.randint(1,20)}}}")
    expr = f"({terms[0]}) + ({terms[1]})" if random.random() > 0.5 else f"({terms[0]}) \\cdot ({terms[1]})"
    return {
        'question_text': f"化簡 ${expr}$",
        'answer': '',
        'correct_answer': f"\\sqrt{{{random.randint(1,20)}}} + \\sqrt{{{random.randint(1,20)}}}",
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}