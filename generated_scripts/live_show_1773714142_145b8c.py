pattern_id = 'p1'
import random

def generate(level=1, **kwargs):
    r1 = random.choice([2, 3, 5, 7])
    den1 = random.choice([2, 3, 5, 8])
    r2 = random.choice([2, 3, 5, 7])
    den2 = random.choice([3, 5, 7, 10])
    question_text = f'\\frac{{\\sqrt{{{r1}}}}}{{{den1}}} \\times \\left(-\\frac{{\\sqrt{{{r2}}}}}{{{den2}}}\\right)'  # [AST Fix: 安全初始化防護]
    expr = sp.Rational(1, den1) * sp.sqrt(r1) * (-sp.Rational(1, den2) * sp.sqrt(r2))
    ans_latex = sp.latex(sp.simplify(expr))
    return {'question_text': question_text, 'correct_answer': ans_latex, 'solution_steps': ['將兩個分數相乘,根號內數字相乘並化簡。'], 'mode': 1}

def check(user_answer, correct_answer):
    return {'correct': str(user_answer).strip() == str(correct_answer).strip(), 'result': '正確'}