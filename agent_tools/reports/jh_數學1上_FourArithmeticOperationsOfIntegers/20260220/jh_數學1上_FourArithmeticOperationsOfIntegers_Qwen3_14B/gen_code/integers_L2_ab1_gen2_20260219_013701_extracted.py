import random

def generate(level=1, **kwargs):
    ops = ['+', '-', '*', '//', 'abs']
    nums = [random.randint(-50, 50) for _ in range(8)]
    parts = []
    
    # 生成括号部分
    a, b = nums[0], nums[1]
    parts.append(f"[({a}{random.choice(ops)}){random.choice(ops)}{b}]")
    
    # 生成除法和乘法部分
    c, d = nums[2], nums[3]
    parts.append(f"÷{c}{random.choice(['×', '÷'])}{d}")
    
    # 生成绝对值部分
    e, f, g = nums[4], nums[5], nums[6]
    abs_expr = f"|{e}{random.choice(['×', '÷'])}{f}{random.choice(['+', '-'])}{g}|"
    parts.append(abs_expr)
    
    # 组合表达式
    question = ''.join(parts)
    # 替换运算符符号
    question = question.replace('÷', '/').replace('×', '*').replace('//', '/')
    
    # 计算正确答案
    try:
        correct = eval(question)
        if not isinstance(correct, int):
            correct = int(correct)
    except:
        correct = 0
    
    return {
        'question_text': question,
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