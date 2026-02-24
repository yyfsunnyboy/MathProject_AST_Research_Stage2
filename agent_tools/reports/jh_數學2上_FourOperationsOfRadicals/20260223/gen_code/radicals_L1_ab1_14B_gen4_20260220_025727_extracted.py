import random
import math

def generate(level=1, **kwargs):
    ops = ['+', '-', '*', '/']
    terms = []
    if level == 1:
        for _ in range(2):
            a = random.randint(2, 20)
            b = random.randint(2, 20)
            terms.append(f"\\sqrt{{{a}}}")
            terms.append(f"\\sqrt{{{b}}}")
        op1 = random.choice(ops)
        op2 = random.choice(ops)
        expr = f"({terms[0]} {op1} {terms[1]}) {op2} ({terms[2]} {op1} {terms[3]})"
    else:
        parts = []
        for _ in range(2):
            a = random.randint(2, 20)
            b = random.randint(2, 20)
            c = random.randint(2, 20)
            d = random.randint(2, 20)
            parts.append(f"\\sqrt{{{a}}} + \\sqrt{{{b}}}")
            parts.append(f"\\sqrt{{{c}}} - \\sqrt{{{d}}}")
        expr = f"({parts[0]})( {parts[1]} ) + \\sqrt{{{random.randint(2, 20)}}}"
    return {
        'question_text': f"化簡 $ {expr} $",
        'answer': '',
        'correct_answer': f"\\sqrt{{{random.randint(2, 20)}}}",
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}