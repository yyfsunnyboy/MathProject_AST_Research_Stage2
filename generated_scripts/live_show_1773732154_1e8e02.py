import random
from sympy import sqrt, simplify, latex

def generate(level=1, **kwargs):
    if level == 1:
        q_type = random.randint(1, 2)
    else:
        q_type = random.randint(1, 4)
    
    if q_type == 1:
        n = random.choice([2, 3, 5, 7, 11])
        a = random.randint(1, 10)
        b = random.randint(1, 10)
        op = random.choice(['+', '-'])
        expr_str = f"{a}\\sqrt{{{n}}} {op} {b}\\sqrt{{{n}}}"
        if op == '+':
            ans = a*sqrt(n) + b*sqrt(n)
        else:
            ans = a*sqrt(n) - b*sqrt(n)
    elif q_type == 2:
        a = random.randint(2, 15)
        b = random.randint(2, 15)
        expr_str = f"\\sqrt{{{a}}} \\times \\sqrt{{{b}}}"
        ans = sqrt(a) * sqrt(b)
    elif q_type == 3:
        a = random.randint(2, 20)
        b = random.randint(2, 10)
        expr_str = f"\\frac{{\\sqrt{{{a}}}}}{{\\sqrt{{{b}}}}}"
        ans = sqrt(a) / sqrt(b)
    else:
        a = random.randint(1, 5)
        b = random.randint(2, 6)
        c = random.randint(2, 10)
        d = random.randint(2, 6)
        expr_str = f"\\frac{{{a}}}{{\\sqrt{{{b}}}}} \\div \\frac{{\\sqrt{{{c}}}}}{{\\sqrt{{{d}}}}}"
        ans = (a/sqrt(b)) / (sqrt(c)/sqrt(d))
    
    return {
        'question_text': f"${expr_str}$",
        'answer': '',
        'correct_answer': str(latex(simplify(ans))),
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}