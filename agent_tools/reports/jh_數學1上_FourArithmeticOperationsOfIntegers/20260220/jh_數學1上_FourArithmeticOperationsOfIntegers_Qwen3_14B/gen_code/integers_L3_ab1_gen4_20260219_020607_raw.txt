import random

def generate(level=1, **kwargs):
    ops = ['+', '-', '×', '÷']
    brackets = ['(', ')']
    abs_symbol = ['|', '|']
    
    # 生成括号内的表达式
    part1 = f"{random.randint(-50, 50)}{random.choice(ops)}{random.randint(-50, 50)}"
    part1 = f"{brackets[0]}{part1}{brackets[1]}"
    
    # 生成绝对值部分
    abs_expr = f"{random.randint(-50, 50)}{random.choice(ops)}{random.randint(-50, 50)}"
    abs_expr = f"{abs_symbol[0]}{abs_expr}{abs_symbol[1]}"
    
    # 组合完整表达式
    expr = f"{part1}{random.choice(ops)}{random.randint(-50, 50)}{random.choice(ops)}{abs_expr}"
    
    # 替换运算符为Python语法
    expr = expr.replace('×', '*').replace('÷', '/')
    
    # 计算正确答案
    try:
        correct_answer = str(int(eval(expr)))
    except:
        return generate(level=1)
    
    return {
        'question_text': expr.replace('*', '×').replace('/', '÷'),
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        user = int(user_answer)
        correct = int(correct_answer)
        return {
            'correct': user == correct,
            'result': '正確' if user == correct else '錯誤'
        }
    except:
        return {
            'correct': False,
            'result': '錯誤'
        }