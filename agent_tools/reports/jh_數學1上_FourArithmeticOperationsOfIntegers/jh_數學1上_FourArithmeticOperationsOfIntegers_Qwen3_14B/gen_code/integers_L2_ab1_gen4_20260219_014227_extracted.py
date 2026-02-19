import random

def generate(level=1, **kwargs):
    ops = ['+', '-', '×', '÷']
    brackets = ['(', ')']
    abs_symbol = '|'
    nums = []
    expr = []
    if level == 1:
        range_min, range_max = -50, 50
    else:
        range_min, range_max = -100, 100

    while len(nums) < 7:
        num = random.randint(range_min, range_max)
        if num != 0 or len(nums) > 0:
            nums.append(num)

    expr.append(f"{nums[0]}")
    for i in range(1, 7):
        op = random.choice(ops)
        if op == '÷':
            while nums[i] == 0:
                nums[i] = random.randint(range_min, range_max)
        if op in ['+', '-']:
            expr.append(f" {op} ")
        else:
            expr.append(f" {op} ")
        expr.append(f"{nums[i]}")
        if i == 3:
            expr.append("÷")
            expr.append(f"abs({nums[4]}×{nums[5]}-{nums[6]})")
            break

    question = ''.join(expr)
    question = question.replace('×', '×').replace('÷', '÷')
    question = question.replace('abs', '|').replace('(', '(').replace(')', ')')

    try:
        correct = eval(question.replace('÷', '/').replace('×', '*').replace('|', 'abs(').replace(')', '))'))
    except:
        return generate(level=level)

    return {
        'question_text': question,
        'answer': '',
        'correct_answer': str(int(correct)),
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        return {
            'correct': user_answer.strip() == correct_answer,
            'result': '正確' if user_answer.strip() == correct_answer else '錯誤'
        }
    except:
        return {'correct': False, 'result': '錯誤'}