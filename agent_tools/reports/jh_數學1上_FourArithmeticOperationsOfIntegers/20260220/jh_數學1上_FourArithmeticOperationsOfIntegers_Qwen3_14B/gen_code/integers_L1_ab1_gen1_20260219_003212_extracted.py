import random

def generate(level=1, **kwargs):
    ops = ['+', '-', '×', '÷']
    abs_expr = f"|{random.randint(-20, -5)}×{random.randint(-10, 10)}-{random.randint(-20, 20)}|"
    bracket1 = f"({random.randint(-50, -10)}{random.choice(ops)}{random.randint(-50, -10)})"
    divisor = random.randint(-10, -1) if random.random() > 0.5 else random.randint(1, 10)
    multiplier = random.randint(1, 10) if random.random() > 0.5 else random.randint(-10, -1)
    
    expr = f"{bracket1}÷{divisor}×{multiplier}+{abs_expr}"
    try:
        result = eval(expr.replace('÷', '/').replace('×', '*'))
        return {
            'question_text': expr,
            'answer': '',
            'correct_answer': str(int(result)),
            'mode': 1
        }
    except:
        return generate(level=1)

def check(user_answer, correct_answer):
    try:
        return {
            'correct': str(int(user_answer)) == correct_answer,
            'result': '正確' if str(int(user_answer)) == correct_answer else '錯誤'
        }
    except:
        return {'correct': False, 'result': '錯誤'}