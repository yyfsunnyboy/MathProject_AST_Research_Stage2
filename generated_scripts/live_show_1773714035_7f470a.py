pattern_id = 'p1'
import random

def generate(level=1, **kwargs):
    r1 = random.choice([2, 3, 5, 7, 11, 13, 17, 19])
    r2 = random.choice([2, 3, 5, 7, 11, 13, 17, 19])
    while r1 == r2:
        r2 = random.choice([2, 3, 5, 7, 11, 13, 17, 19])
    question_text = f'\\sqrt{{{r1}}} \\times \\sqrt{{{r2}}}'  # [AST Fix: 安全初始化防護]
    expr = sp.sqrt(r1) * sp.sqrt(r2)
    ans_latex = sp.latex(sp.simplify(expr))
    return {'question_text': question_text, 'correct_answer': ans_latex, 'solution_steps': ['根號內數字相乘,並化簡為最簡根式。'], 'mode': 1}

def check(user_answer, correct_answer):
    return {'correct': str(user_answer).strip() == str(correct_answer).strip(), 'result': '正確'}