import random
from sympy import sqrt, simplify, latex

def generate(level=1, **kwargs):
    rads = [2, 3, 5, 6, 7, 10, 11, 13, 14, 15]
    r = random.sample(rads, 3)
    c = [random.randint(1, 5) for _ in range(4)]
    
    if level == 1:
        t1 = c[0] * sqrt(r[0])
        t2 = c[1] * sqrt(r[0])
        expr = t1 + t2
        q_text = f"${latex(t1)} + {latex(t2)}$"
    elif level == 2:
        term1 = sqrt(r[0]) + sqrt(r[1])
        term2 = sqrt(r[2]) - c[0]
        expr = term1 * term2
        q_text = f"$({latex(term1)})({latex(term2)})$"
    else:
        num = c[0]
        den = sqrt(r[0]) + c[1]
        expr = num / den
        q_text = f"$\\frac{{{num}}}{{{latex(den)}}}$"
        
    ans_expr = simplify(expr)
    return {
        'question_text': q_text,
        'answer': '',
        'correct_answer': str(latex(ans_expr)),
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}