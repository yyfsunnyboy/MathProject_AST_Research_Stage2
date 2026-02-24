import random
import math

def generate(level=1, **kwargs):
    ops = ['+', '-', '*']
    terms = []
    for _ in range(2):
        a = random.randint(2, 20)
        b = random.randint(2, 20)
        c = random.randint(2, 20)
        d = random.randint(2, 20)
        term = f"\\sqrt{{{a}}} + \\sqrt{{{b}}} - \\sqrt{{{c}}} + \\sqrt{{{d}}}"
        terms.append(term)
    expr = f"({terms[0]}) {random.choice(ops)} ({terms[1]})"
    question_text = f"化簡 ${expr}$"
    correct_answer = simplify(expr)
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}

def simplify(expr):
    parts = expr.split()
    terms = []
    for i in range(0, len(parts), 2):
        coeff = 1
        radicand = int(parts[i+1][1:-1])
        if parts[i] == '-':
            coeff = -1
        elif parts[i] == '+':
            coeff = 1
        terms.append((coeff, radicand))
    simplified = {}
    for coeff, radicand in terms:
        sqrt_radicand = math.isqrt(radicand)
        if sqrt_radicand * sqrt_radicand == radicand:
            simplified[radicand] = simplified.get(radicand, 0) + coeff * sqrt_radicand
        else:
            simplified[radicand] = simplified.get(radicand, 0) + coeff
    result = []
    for radicand, coeff in sorted(simplified.items()):
        if coeff != 0:
            if coeff == 1:
                result.append(f"\\sqrt{{{radicand}}}")
            elif coeff == -1:
                result.append(f"-\\sqrt{{{radicand}}}")
            else:
                result.append(f"{coeff}\\sqrt{{{radicand}}}")
    return " + ".join(result) if result else "0"