import random
import math

def generate(level=1, **kwargs):
    a = random.randint(1, 10)
    b = random.randint(1, 10)
    c = random.randint(1, 10)
    d = random.randint(1, 10)
    e = random.randint(1, 10)
    f = random.randint(1, 10)
    g = random.randint(1, 10)
    h = random.randint(1, 10)
    i = random.randint(1, 10)
    
    sign1 = random.choice(['+', '-'])
    sign2 = random.choice(['+', '-'])
    sign3 = random.choice(['+', '-'])
    sign4 = random.choice(['+', '-'])
    
    question = f"計算 $[{sign1}{a}×{b}/{c} + {d}÷{e}/{f}] ÷ ({g}/{h}{sign2}{i})$ 的值。"
    correct_answer = str(eval(f"({a}*{b}/{c} + {d}/{e}/{f}) / ({g}/{h}{sign2}{i})"))
    return {
        'question_text': question,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        user = float(user_answer)
        correct = float(correct_answer)
        return {'correct': abs(user - correct) < 1e-9, 'result': '正確' if abs(user - correct) < 1e-9 else '錯誤'}
    except:
        return {'correct': False, 'result': '錯誤'}