import random
import math

def generate(level=1, **kwargs):
    question = ''
    terms = []
    operations = ['+', '-']
    
    if level == 1:
        num_terms = random.randint(2, 4)
        for _ in range(num_terms):
            coeff = random.randint(1, 5)
            radicand = random.choice([2, 3, 5, 6, 7, 8, 10])
            terms.append(f"{coeff}\\sqrt{{{radicand}}}")
        question = ' + '.join(terms)
    elif level == 2:
        num_terms = random.randint(2, 3)
        for _ in range(num_terms):
            coeff = random.randint(1, 5)
            radicand = random.choice([2, 3, 5, 6, 7, 8, 10])
            terms.append(f"{coeff}\\sqrt{{{radicand}}}")
        question = ' + '.join(terms)
        if random.random() < 0.5:
            term1 = f"\\sqrt{{{random.choice([2, 3, 5, 6, 7, 8, 10])}}}"
            term2 = f"\\sqrt{{{random.choice([2, 3, 5, 6, 7, 8, 10])}}}"
            question += f" + ({term1} + {term2})(\\sqrt{{{random.choice([2, 3, 5, 6, 7, 8, 10])}}})" if random.random() < 0.5 else f" + ({term1} - {term2})(\\sqrt{{{random.choice([2, 3, 5, 6, 7, 8, 10])}}})"
    
    return {
        'question_text': f"化簡 $ {question} $",
        'answer': '',
        'correct_answer': 'placeholder',
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}