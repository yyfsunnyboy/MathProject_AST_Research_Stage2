import random
from fractions import Fraction

def generate(level=1, **kwargs):
    def generate_bracket():
        ops = ['+', '-', '\\times', '\\div']
        nums = [random.randint(-100, 100) for _ in range(3)]
        nums[0] = random.choice([x for x in nums if x != 0])
        nums[1] = random.choice([x for x in nums if x != 0])
        nums[2] = random.choice([x for x in nums if x != 0])
        expr = f'({nums[0]} {random.choice(ops)} {nums[1]} {random.choice(ops)} {nums[2]})'
        return expr

    def generate_abs():
        ops = ['+', '-', '\\times', '\\div']
        nums = [random.randint(-100, 100) for _ in range(3)]
        nums[0] = random.choice([x for x in nums if x != 0])
        nums[1] = random.choice([x for x in nums if x != 0])
        nums[2] = random.choice([x for x in nums if x != 0])
        expr = f'|{nums[0]} {random.choice(ops)} {nums[1]} {random.choice(ops)} {nums[2]}|'
        return expr

    bracket = generate_bracket()
    abs_expr = generate_abs()
    question_text = f'計算 $$ {bracket} + {abs_expr} $$ 的值。'
    answer = eval(bracket + ' + ' + abs_expr)
    correct_answer = str(answer)
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        if str(user_answer).strip() == str(correct_answer).strip():
            return {'correct': True, 'result': '正確'}
        
        ua = Fraction(user_answer) if '/' in str(user_answer) else float(user_answer)
        ca = Fraction(correct_answer) if '/' in str(correct_answer) else float(correct_answer)
        
        if abs(ua - ca) < 1e-6:
            return {'correct': True, 'result': '正確'}
        
        return {'correct': False, 'result': '錯誤'}
    except:
        return {
            'correct': str(user_answer).strip() == str(correct_answer).strip(),
            'result': '正確' if str(user_answer).strip() == str(correct_answer).strip() else '錯誤'
        }