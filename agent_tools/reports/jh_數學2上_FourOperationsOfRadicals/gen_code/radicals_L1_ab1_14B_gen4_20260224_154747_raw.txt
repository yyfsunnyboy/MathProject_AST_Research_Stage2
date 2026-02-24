import random
import math

def generate(level=1, **kwargs):
    question_text = ''
    answer = ''
    correct_answer = ''
    mode = 1
    
    if level == 1:
        a = random.randint(2, 10)
        b = random.randint(2, 10)
        c = random.randint(2, 10)
        d = random.randint(2, 10)
        e = random.randint(2, 10)
        f = random.randint(2, 10)
        op1 = random.choice(['+', '-'])
        op2 = random.choice(['+', '-'])
        op3 = random.choice(['+', '-'])
        op4 = random.choice(['+', '-'])
        op5 = random.choice(['+', '-'])
        
        sqrt1 = math.sqrt(a)
        sqrt2 = math.sqrt(b)
        sqrt3 = math.sqrt(c)
        sqrt4 = math.sqrt(d)
        sqrt5 = math.sqrt(e)
        sqrt6 = math.sqrt(f)
        
        question_text = f"化簡 $({op1}\\sqrt{{{a}}} + {op2}\\sqrt{{{b}}} - {op3}\\sqrt{{{c}}}) + ({op4}\\sqrt{{{d}}} + {op5}\\sqrt{{{e}}})(\\sqrt{{{f}}} - 1)$"
        answer = f"{op1}\\sqrt{{{a}}} + {op2}\\sqrt{{{b}}} - {op3}\\sqrt{{{c}}} + {op4}\\sqrt{{{d}}}\\sqrt{{{f}}} + {op5}\\sqrt{{{e}}}\\sqrt{{{f}}} - {op4}\\sqrt{{{d}}} - {op5}\\sqrt{{{e}}}"
        correct_answer = answer
    return {'question_text': question_text, 'answer': answer, 'correct_answer': correct_answer, 'mode': mode}

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}