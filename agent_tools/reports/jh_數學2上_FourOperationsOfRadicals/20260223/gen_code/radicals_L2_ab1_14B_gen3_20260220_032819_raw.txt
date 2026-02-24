import random
import math

def generate(level=1, **kwargs):
    ops = ['+', '-', '*', '/']
    terms = []
    for _ in range(2 if level == 1 else 3):
        a = random.randint(2, 20)
        b = random.randint(2, 20)
        terms.append(f"\\sqrt{{{a}}}")
        terms.append(f"\\sqrt{{{b}}}")
    expr = []
    for _ in range(2 if level == 1 else 3):
        expr.append(terms.pop(random.randint(0, len(terms)-1)))
        expr.append(ops[random.randint(0, 3)])
    expr.pop()
    expr = ' '.join(expr)
    expr = f"({expr}) + ({expr})" if level == 1 else f"({expr}) * ({expr})"
    return {
        'question_text': f"化簡 ${expr}$",
        'answer': '',
        'correct_answer': f"\\sqrt{{{random.randint(2, 20)}}}",
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}