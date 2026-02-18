import random
import math

def generate(level=1, **kwargs):
    ops = ['+', '-', '*', '/']
    terms = []
    
    if level == 1:
        radicals = [random.randint(2, 50) for _ in range(4)]
        terms.append(f"\\sqrt{{{radicals[0]}}}")
        terms.append(f"\\sqrt{{{radicals[1]}}}")
        terms.append(f"\\sqrt{{{radicals[2]}}}")
        terms.append(f"\\sqrt{{{radicals[3]}}}")
        
        expr = f"({terms[0]} {random.choice(ops)} {terms[1]} {random.choice(ops)} {terms[2]}) {random.choice(ops)} ({terms[3]} {random.choice(ops)} {terms[0]})"
    else:
        radicals = [random.randint(2, 100) for _ in range(6)]
        terms = [f"\\sqrt{{{r}}}" for r in radicals]
        expr = f"(({terms[0]} {random.choice(ops)} {terms[1]} {random.choice(ops)} {terms[2]}) {random.choice(ops)} ({terms[3]} {random.choice(ops)} {terms[4]})) {random.choice(ops)} {terms[5]}"
    
    question = f"化簡 ${expr}$"
    answer = simplify(expr)
    return {
        'question_text': question,
        'answer': '',
        'correct_answer': answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    user = user_answer.replace(' ', '').lower()
    correct = correct_answer.replace(' ', '').lower()
    return {
        'correct': user == correct,
        'result': '正確' if user == correct else '錯誤'
    }

def simplify(expr):
    expr = expr.replace('sqrt', 'math.sqrt')
    expr = expr.replace('{', '(').replace('}', ')')
    try:
        result = eval(expr)
        if isinstance(result, float):
            if result.is_integer():
                return f"{int(result)}"
            else:
                return f"{result:.4f}"
        else:
            return f"{result:.4f}"
    except:
        return expr