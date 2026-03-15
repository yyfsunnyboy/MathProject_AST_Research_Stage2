import random

def p2b_mult_distrib():
    a = random.randint(2, 9)
    b = random.randint(2, 9)
    c = random.randint(2, 9)
    question = f'\\text{{Calculate: }}{a}\\times({b}+{c})'
    correct = f'\\text{{Answer: }}{a*b + a*c}'
    return {'question_text': question, 'correct_answer': correct}

def check(user_answer, correct_answer):
    try:
        return {'correct': str(user_answer).strip() == str(correct_answer).strip(), 'result': '自動補全比對'}
    except:
        return {'correct': False, 'result': '錯誤'}

def generate():
    try:
        return p2b_mult_distrib()
    except:
        return {'question_text': 'Fallback due to severe hallucination', 'correct_answer': '\\text{Failed}'}