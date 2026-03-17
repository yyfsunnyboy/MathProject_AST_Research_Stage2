import random
import sympy

def generate(level=1, **kwargs):
    pool = [8, 12, 18, 20, 24, 27, 28, 32, 40, 44, 45, 48, 50, 52, 54, 60, 63, 68, 72, 75, 80, 84, 88, 90, 92, 96, 98, 99]
    if level == 1:
        n1 = random.choice(pool)
        n2 = random.choice(pool)
        n3 = random.choice(pool)
        n4 = random.choice(pool)
        expr = sympy.sqrt(n1) + sympy.sqrt(n2) - sympy.sqrt(n3) + sympy.sqrt(n4)
        latex_q = f"\\sqrt{{{n1}}} + \\sqrt{{{n2}}} - \\sqrt{{{n3}}} + \\sqrt{{{n4}}}"
    elif level == 2:
        n1 = random.randint(2, 20)
        n2 = random.randint(2, 20)
        if random.choice([True, False]):
            expr = sympy.sqrt(n1) * sympy.sqrt(n2)
            latex_q = f"\\sqrt{{{n1}}} \\times \\sqrt{{{n2}}}"
        else:
            n2 = random.randint(2, 10)
            n1 = n2 * random.randint(2, 5)
            expr = sympy.sqrt(n1) / sympy.sqrt(n2)
            latex_q = f"\\sqrt{{{n1}}} \\div \\sqrt{{{n2}}}"
    else:
        n1 = random.randint(2, 10)
        n2 = random.randint(2, 10)
        n3 = random.randint(2, 10)
        expr = sympy.sqrt(n1) * (sympy.sqrt(n2) + sympy.sqrt(n3))
        latex_q = f"\\sqrt{{{n1}}}(\\sqrt{{{n2}}} + \\sqrt{{{n3}}})"
    
    return {
        'question_text': f"${latex_q}$",
        'answer': '',
        'correct_answer': str(sympy.latex(expr)),
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': 'Correct' if correct else 'Wrong'}