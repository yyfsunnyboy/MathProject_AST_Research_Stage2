import random
import math

def generate(level=1, **kwargs):
    question = []
    terms = []
    operations = ['+', '-']
    
    if level == 1:
        num_terms = random.randint(2, 4)
        for _ in range(num_terms):
            coeff = random.randint(1, 5)
            radicand = random.randint(2, 20)
            terms.append(f"{coeff}\\sqrt{{{radicand}}}")
        question.append(" + ".join(terms))
        
        num_terms = random.randint(1, 2)
        for _ in range(num_terms):
            coeff1 = random.randint(1, 3)
            radicand1 = random.randint(2, 20)
            coeff2 = random.randint(1, 3)
            radicand2 = random.randint(2, 20)
            term = f"({coeff1}\\sqrt{{{radicand1}}} {random.choice(operations)} {coeff2}\\sqrt{{{radicand2}}})"
            question.append(term)
        
        question_text = "化簡 $" + " + ".join(question) + "$"
        answer = ""
        correct_answer = ""
        
        return {
            'question_text': question_text,
            'answer': answer,
            'correct_answer': correct_answer,
            'mode': 1
        }
    
    if level == 2:
        num_terms = random.randint(2, 4)
        for _ in range(num_terms):
            coeff = random.randint(1, 5)
            radicand = random.randint(2, 20)
            terms.append(f"{coeff}\\sqrt{{{radicand}}}")
        question.append(" + ".join(terms))
        
        num_terms = random.randint(1, 2)
        for _ in range(num_terms):
            coeff1 = random.randint(1, 3)
            radicand1 = random.randint(2, 20)
            coeff2 = random.randint(1, 3)
            radicand2 = random.randint(2, 20)
            term = f"({coeff1}\\sqrt{{{radicand1}}} {random.choice(operations)} {coeff2}\\sqrt{{{radicand2}}})"
            question.append(term)
        
        question_text = "化簡 $" + " + ".join(question) + "$"
        answer = ""
        correct_answer = ""
        
        return {
            'question_text': question_text,
            'answer': answer,
            'correct_answer': correct_answer,
            'mode': 1
        }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}