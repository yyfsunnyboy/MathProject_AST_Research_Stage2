import random
import math

def generate(level=1, **kwargs):
    ops = ['+', '-', '*', '/']
    terms = []
    
    for _ in range(2):
        a = random.randint(2, 20)
        b = random.randint(2, 20)
        c = random.randint(2, 20)
        d = random.randint(2, 20)
        op1 = random.choice(ops)
        op2 = random.choice(ops)
        
        if op1 == '+':
            terms.append(f"\\sqrt{{{a}}} {op1} \\sqrt{{{b}}}")
        elif op1 == '-':
            terms.append(f"\\sqrt{{{a}}} {op1} \\sqrt{{{b}}}")
        elif op1 == '*':
            terms.append(f"(\\sqrt{{{a}}} {op1} \\sqrt{{{b}}})")
        else:
            terms.append(f"\\frac{{\\sqrt{{{a}}}}}{{\\sqrt{{{b}}}}}")
    
    expr = f"({terms[0]}) {random.choice(ops)} ({terms[1]})"
    question_text = f"化簡 ${expr}$"
    
    parts = expr.split()
    num_parts = len(parts)
    values = []
    
    for i in range(num_parts):
        if parts[i].startswith('\\sqrt'):
            val = float(parts[i][5:-1])
            values.append(math.sqrt(val))
        else:
            values.append(float(parts[i]))
    
    result = values[0]
    for i in range(1, num_parts, 2):
        op = parts[i]
        next_val = values[i+1]
        
        if op == '+':
            result += next_val
        elif op == '-':
            result -= next_val
        elif op == '*':
            result *= next_val
        else:
            result /= next_val
    
    correct_answer = f"{result:.2f}"
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}