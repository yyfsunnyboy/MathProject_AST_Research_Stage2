import random
import math

def generate(level=1, **kwargs):
    ops = ['+', '-', '÷', '×']
    brackets = ['(', ')']
    abs_symbols = ['|', '|']
    
    # 生成括号内表达式
    a = random.randint(-20, 20)
    b = random.randint(-20, 20)
    c = random.choice([random.randint(-10, -1), random.randint(1, 10)])
    d = random.randint(-10, 10)
    
    # 生成绝对值部分
    e = random.randint(-10, 10)
    f = random.randint(-10, 10)
    g = random.randint(-20, 20)
    
    # 构建题目字符串
    question = f"[({a}{brackets[0]}{b}{brackets[1]}]{ops[2]}{c}{ops[3]}{d}+{abs_symbols[0]}{e}{ops[3]}{f}{ops[1]}{g}{abs_symbols[1]}"
    
    # 计算正确答案
    expr = f"(({a}+{b})/{c}*{d}+abs({e}*{f}-{g}))"
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
            'correct': int(user_answer) == int(correct_answer),
            'result': '正確' if int(user_answer) == int(correct_answer) else '錯誤'
        }
    except:
        return {
            'correct': False,
            'result': '錯誤'
        }