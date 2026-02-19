import random

def generate(level=1, **kwargs):
    ops = ['+', '-', '×', '÷']
    num_range = (-50, 50)
    
    # 生成括号内部分
    part1 = f"({random.randint(*num_range)}{random.choice(ops)}{random.randint(*num_range)})"
    
    # 生成绝对值部分
    abs_expr = f"|{random.randint(*num_range)}×{random.randint(*num_range)}{random.choice(ops)}{random.randint(*num_range)}|"
    
    # 组合完整题目
    question = f"{part1}{random.choice(ops)}{random.randint(*num_range)}×{random.randint(*num_range)}+{abs_expr}"
    
    # 计算正确答案
    expr = question.replace('×', '*').replace('÷', '/')
    correct_answer = str(eval(expr))
    
    return {
        'question_text': question,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        return {
            'correct': int(user_answer) == int(correct_answer),
            'result': '正確' if int(user_answer) == int(correct_answer) else '錯誤'
        }
    except:
        return {
            'correct': False,
            'result': '錯誤'
        }