import random
import math

def generate(level=1, **kwargs):
    question = ''
    answer = ''
    correct_answer = ''
    mode = 1
    if level == 1:
        a = random.randint(2, 10)
        b = random.randint(2, 10)
        c = random.randint(2, 10)
        d = random.randint(2, 10)
        e = random.randint(2, 10)
        f = random.randint(2, 10)
        g = random.randint(2, 10)
        h = random.randint(2, 10)
        i = random.randint(2, 10)
        j = random.randint(2, 10)
        k = random.randint(2, 10)
        l = random.randint(2, 10)
        m = random.randint(2, 10)
        n = random.randint(2, 10)
        o = random.randint(2, 10)
        p = random.randint(2, 10)
        q = random.randint(2, 10)
        r = random.randint(2, 10)
        s = random.randint(2, 10)
        t = random.randint(2, 10)
        u = random.randint(2, 10)
        v = random.randint(2, 10)
        w = random.randint(2, 10)
        x = random.randint(2, 10)
        y = random.randint(2, 10)
        z = random.randint(2, 10)
        question += f"$(\\sqrt{{{a}}} + \\sqrt{{{b}}} - {c}\\sqrt{{{d}}}) + (\\sqrt{{{e}}} + \\sqrt{{{f}}})(\\sqrt{{{g}}} - 1)$"
        answer = f"\\sqrt{{{a}}} + \\sqrt{{{b}}} - {c}\\sqrt{{{d}}} + (\\sqrt{{{e}}} + \\sqrt{{{f}}})(\\sqrt{{{g}}} - 1)"
        correct_answer = f"\\sqrt{{{a}}} + \\sqrt{{{b}}} - {c}\\sqrt{{{d}}} + (\\sqrt{{{e}}} + \\sqrt{{{f}}})(\\sqrt{{{g}}} - 1)"
    return {'question_text': question, 'answer': answer, 'correct_answer': correct_answer, 'mode': mode}

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}