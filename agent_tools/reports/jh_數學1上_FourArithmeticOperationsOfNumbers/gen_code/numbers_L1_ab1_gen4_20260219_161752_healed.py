import random
import math

def generate(level=1, **kwargs):
    ops = ['+', '-', '×', '÷']
    fractions = []
    
    for _ in range(2):
        numerator = random.randint(1, 10 if level == 1 else 20)
        denominator = random.randint(1, 10 if level == 1 else 20)
        sign = random.choice(['', '-'])
        fractions.append(f"{sign}{numerator}/{denominator}")
    
    part1 = f"({random.choice(fractions)}{random.choice(ops)}{random.choice(fractions)})"
    part2 = f"{random.choice(fractions)}{random.choice(ops)}{random.choice(fractions)}"
    part3 = f"|{random.choice(fractions)}{random.choice(ops)}{random.choice(fractions)}|"
    
    question = f"計算 ${part1}{random.choice(ops)}{part2} + {part3}$ 的值"
    
    # Calculate correct answer
    def eval_fraction(expr):
        expr = expr.replace('×', '*').replace('÷', '/')
        return eval(expr)
    
    try:
        ans = eval_fraction(part1) * eval_fraction(part2) / eval_fraction(part3)
        correct_answer = f"{ans}"
    except:
        correct_answer = "無解"
    
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
        return {'correct': math.isclose(user, correct, rel_tol=1e-9), 'result': '正確' if math.isclose(user, correct, rel_tol=1e-9) else '錯誤'}
    except:
        return {'correct': False, 'result': '錯誤'}