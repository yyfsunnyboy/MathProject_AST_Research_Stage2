import random
import math

def generate(level=1, **kwargs):
    ops = ['+', '-', '*', '/']
    terms = []
    for _ in range(random.randint(2,4)):
        a = random.randint(1, 20)
        b = random.randint(1, 20)
        op = random.choice(ops)
        if op == '+':
            terms.append(f"\\sqrt{{{a}}} + \\sqrt{{{b}}}")
        elif op == '-':
            terms.append(f"\\sqrt{{{a}}} - \\sqrt{{{b}}}")
        elif op == '*':
            terms.append(f"(\\sqrt{{{a}}} + \\sqrt{{{b}}})(\\sqrt{{{a}}} - \\sqrt{{{b}}})")
        else:
            terms.append(f"\\frac{{\\sqrt{{{a}}}}}{{\\sqrt{{{b}}}}}")
    
    expr = " + ".join(terms)
    correct = eval(expr.replace('sqrt', 'math.sqrt'))
    simplified = simplify(correct)
    return {
        'question_text': f"化簡 ${expr}$",
        'answer': '',
        'correct_answer': simplified,
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}

def simplify(expr):
    if isinstance(expr, (int, float)):
        return f"{expr}"
    if isinstance(expr, tuple):
        return simplify(expr[0]) + " + " + simplify(expr[1])
    if isinstance(expr, list):
        return " + ".join([simplify(x) for x in expr])
    return f"{expr}"