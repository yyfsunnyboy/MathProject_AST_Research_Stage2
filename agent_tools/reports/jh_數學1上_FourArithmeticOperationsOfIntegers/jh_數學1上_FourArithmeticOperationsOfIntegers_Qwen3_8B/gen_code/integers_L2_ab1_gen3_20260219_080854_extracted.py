import random

def generate(level=1, **kwargs):
    operators = ['+', '-', '×', '÷']
    nums = []
    
    if level == 1:
        nums = [random.randint(-20, 20) for _ in range(4)]
    elif level == 2:
        nums = [random.randint(-100, 100) for _ in range(4)]
    else:
        nums = [random.randint(-500, 500) for _ in range(4)]
    
    # 生成主表达式
    expr_parts = []
    for i in range(3):
        op = random.choice(operators)
        expr_parts.append(f'({nums[i]}{op}{nums[i+1]})')
    
    # 生成绝对值部分
    abs_expr = f'|{nums[3]}×({nums[0]}-{nums[1]})-{nums[2]}|'
    
    # 组合完整表达式
    full_expr = f'[{expr_parts[0]}÷{expr_parts[1]}×{expr_parts[2]}]+{abs_expr}'
    full_expr = full_expr.replace('×', '×').replace('÷', '÷').replace('+', '+').replace('-', '-')
    
    # 计算正确答案
    try:
        correct = eval(full_expr.replace('×', '*').replace('÷', '/').replace('|', 'abs(').replace(')', ')+abs('))
    except:
        correct = 0
    
    return {
        'question_text': f'計算 [{expr_parts[0]}÷{expr_parts[1]}×{expr_parts[2]}]+{abs_expr} 的值',
        'answer': '',
        'correct_answer': str(correct),
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        user = int(user_answer.strip())
        correct = int(correct_answer)
        return {'correct': user == correct, 'result': '正確' if user == correct else '錯誤'}
    except:
        return {'correct': False, 'result': '錯誤'}