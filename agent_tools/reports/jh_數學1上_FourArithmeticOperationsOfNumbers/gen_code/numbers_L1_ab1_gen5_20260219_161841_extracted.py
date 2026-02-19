import random
import math

def generate(level=1, **kwargs):
    ops = ['+', '-', '×', '÷']
    fractions = []
    for _ in range(4):
        numerator = random.randint(1, 10) * random.choice([-1, 1])
        denominator = random.randint(1, 10)
        fractions.append(f"{numerator}/{denominator}")
    
    part1 = f"({random.choice(fractions)}{random.choice(ops)}{random.choice(fractions)})"
    part2 = f"{random.choice(fractions)}{random.choice(ops)}{random.choice(fractions)}"
    abs_part = f"|{random.choice(fractions)}{random.choice(ops)}{random.choice(fractions)}|"
    
    question = f"計算 ${part1}÷{random.choice(fractions)} + {abs_part}$ 的值"
    
    # Calculate correct answer
    def eval_fraction(expr):
        expr = expr.replace('×', '*').replace('÷', '/')
        return eval(expr)
    
    try:
        correct = eval_fraction(f"({eval_fraction(part1)}/{random.choice(fractions)}) + {abs_part}")
        correct = f"{correct:.4f}" if not correct.is_integer() else f"{int(correct)}"
    except:
        correct = "錯誤"
    
    return {
        'question_text': question,
        'answer': '',
        'correct_answer': correct,
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        user = float(user_answer)
        correct = float(correct_answer)
        return {'correct': math.isclose(user, correct, rel_tol=1e-4), 'result': '正確' if math.isclose(user, correct, rel_tol=1e-4) else '錯誤'}
    except:
        return {'correct': False, 'result': '錯誤'}