import random
import math

def generate(level=1, **kwargs):
    ops = ['+', '-', '÷', '×']
    brackets = []
    abs_expr = []
    
    # 生成括号内表达式
    a = random.randint(-50, 50)
    b = random.randint(-50, 50)
    op1 = random.choice(ops[:2])
    bracket_expr = f"({a}{op1}{b})"
    
    # 生成除法和乘法部分
    c = random.randint(-20, 20)
    while c == 0:
        c = random.randint(-20, 20)
    d = random.randint(-20, 20)
    bracket_expr += f"÷({c})×{d}"
    
    # 生成绝对值部分
    e = random.randint(-20, 20)
    f = random.randint(-20, 20)
    g = random.randint(-20, 20)
    abs_expr = f"|{e}×({f})-{g}|"
    
    # 组合完整题目
    question = f"{bracket_expr}+{abs_expr}"
    
    # 计算正确答案
    expr = question.replace('÷', '/').replace('×', '*').replace('|', 'abs(').replace('abs(', 'abs(')
    correct_answer = str(int(eval(expr)))
    
    return {
        'question_text': question,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        return {
            'correct': user_answer == correct_answer,
            'result': '正確' if user_answer == correct_answer else '錯誤'
        }
    except:
        return {
            'correct': False,
            'result': '錯誤'
        }