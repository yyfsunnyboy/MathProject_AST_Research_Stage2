import random
import math

def generate(level=1, **kwargs):
    ops = ['+', '-', '×', '÷']
    fractions = []
    for _ in range(2):
        a = random.randint(1, 10)
        b = random.randint(1, 10)
        while math.gcd(a, b) != 1:
            a = random.randint(1, 10)
            b = random.randint(1, 10)
        fractions.append(f"{a}/{b}")
    
    part1 = f"({random.randint(-5,5)}{random.choice(ops)}{fractions[0]})"
    part2 = f"{random.choice(ops)}{fractions[1]}"
    part3 = f"|{random.randint(-5,5)}×({fractions[0]}{random.choice(ops)}{fractions[1]})|"
    
    question = f"計算 $${part1}{part2} {part3}$$ 的值"
    
    # Calculate correct answer
    def eval_frac(expr):
        expr = expr.replace('×', '*').replace('÷', '/')
        return eval(expr)
    
    try:
        ans = eval_frac(f"{part1}{part2} + {part3}")
        if ans.denominator == 1:
            correct_answer = str(ans.numerator)
        else:
            correct_answer = f"{ans.numerator}/{ans.denominator}"
    except:
        correct_answer = "0"
    
    return {
        'question_text': question,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        user = user_answer.replace(' ', '').replace('÷', '/').replace('×', '*')
        correct = correct_answer.replace(' ', '').replace('÷', '/').replace('×', '*')
        return {
            'correct': user == correct,
            'result': '正確' if user == correct else '錯誤'
        }
    except:
        return {'correct': False, 'result': '錯誤'}