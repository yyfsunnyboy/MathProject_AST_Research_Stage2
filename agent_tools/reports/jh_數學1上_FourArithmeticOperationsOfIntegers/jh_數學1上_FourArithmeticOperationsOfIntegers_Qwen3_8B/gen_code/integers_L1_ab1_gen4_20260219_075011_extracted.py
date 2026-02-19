import random

def generate(level=1, **kwargs):
    ops = ['+', '-', '×', '÷']
    nums = [random.randint(-100, 100) for _ in range(5)]
    expr = f"[{nums[0]}{random.choice(ops)}{nums[1]}]÷{nums[2]}×{nums[3]} + |{nums[4]}×{nums[0]} - {nums[1]}|"
    try:
        correct = eval(expr.replace('÷', '/').replace('×', '*').replace('|', '').replace('}', '').replace('{', ''))
    except:
        correct = 0
    return {
        'question_text': expr,
        'answer': '',
        'correct_answer': str(correct),
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        user = int(user_answer)
        correct = int(correct_answer)
        return {'correct': user == correct, 'result': '正確' if user == correct else '錯誤'}
    except:
        return {'correct': False, 'result': '錯誤'}