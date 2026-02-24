import random
import math

def generate(level=1, **kwargs):
    ops = ['+', '-', '×', '÷']
    if level == 1:
        num_range = (1, 20)
    else:
        num_range = (1, 50)
    
    def generate_expr():
        a = random.randint(*num_range)
        b = random.randint(*num_range)
        op = random.choice(ops)
        if op == '+':
            expr = f"{a}+{b}"
        elif op == '-':
            expr = f"{a}-{b}"
        elif op == '×':
            expr = f"{a}×{b}"
        else:
            expr = f"{a}÷{b}"
        return expr
    
    part1 = generate_expr()
    part2 = generate_expr()
    abs_expr = generate_expr()
    
    question = f"計算 [{part1}]÷{part2}×3+|{abs_expr}|"
    correct_answer = str(eval(question.replace('×', '*').replace('÷', '/').replace('|', '').replace('×', '*').replace('÷', '/')))
    return {
        'question_text': question,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        user_num = int(user_answer)
        correct_num = int(correct_answer)
        return {'correct': user_num == correct_num, 'result': '正確' if user_num == correct_num else '錯誤'}
    except:
        return {'correct': False, 'result': '錯誤'}