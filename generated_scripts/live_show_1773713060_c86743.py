python
import random

def generate(level=1, **kwargs):
    r1 = random.choice([2, 3, 5, 7])
    r2 = random.choice([2, 3, 5, 7])
    c1 = random.choice([1, 2, 3, 4])
    c2 = random.choice([1, 2, 3, 4])
    question_text = f'{c1}\\sqrt{{{r1}}} \\times {c2}\\sqrt{{{r2}}}'  # [AST Fix: 安全初始化防護]
    expr = c1 * sp.sqrt(r1) * c2 * sp.sqrt(r2)
    ans_latex = sp.latex(sp.simplify(expr))
    return {'question_text': question_text, 'correct_answer': ans_latex, 'solution_steps': ['將係數相乘,根號內數字相乘並化簡。'], 'mode': 1}

def check(user_answer, correct_answer):
    return {'correct': str(user_answer).strip() == str(correct_answer).strip(), 'result': '正確'}