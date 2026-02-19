import random
import math

def generate(level=1, **kwargs):
    ops = ['+', '-', '×', '÷']
    signs = ['+', '-']
    fractions = []
    
    for _ in range(2):
        numerator = random.randint(1, 10)
        denominator = random.randint(1, 10)
        if denominator == numerator:
            denominator += 1
        sign = random.choice(signs)
        fractions.append(f"{sign}{numerator}/{denominator}")
    
    part1 = f"({random.choice(fractions)}{random.choice(ops)}{random.choice(fractions)})"
    part2 = f"{random.choice(fractions)}{random.choice(ops)}{random.choice(fractions)}"
    part3 = f"{random.choice(fractions)}{random.choice(ops)}{random.choice(fractions)}"
    
    question = f"計算 $[{part1}]{random.choice(ops)}{part2} + |{part3}|$ 的值。"
    
    # Calculate correct answer
    def calc(expr):
        expr = expr.replace('×', '*').replace('÷', '/')
        return eval(expr)
    
    try:
        answer = calc(f"{part1}{random.choice(ops)}{part2} + abs({part3})")
        answer = f"{answer}" if answer.is_integer() else f"{answer:.2f}"
    except:
        answer = "0"
    
    return {
        'question_text': question,
        'answer': '',
        'correct_answer': answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        user = float(user_answer)
        correct = float(correct_answer)
        return {'correct': abs(user - correct) < 1e-6, 'result': '正確' if abs(user - correct) < 1e-6 else '錯誤'}
    except:
        return {'correct': False, 'result': '錯誤'}