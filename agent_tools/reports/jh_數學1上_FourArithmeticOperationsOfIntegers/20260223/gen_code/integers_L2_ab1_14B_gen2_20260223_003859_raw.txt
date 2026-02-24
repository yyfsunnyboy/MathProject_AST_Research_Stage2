import random
import math

def generate(level=1, **kwargs):
    ops = ['+', '-', '×', '÷']
    brackets = ['(', ')']
    abs_symbol = '│'
    
    # 生成基本表达式
    expr = []
    numbers = [random.randint(-20, 20) for _ in range(4)]
    
    # 添加括号和绝对值
    if random.random() > 0.5:
        expr.append(brackets[0])
        expr.append(str(numbers[0]))
        expr.append(random.choice(ops))
        expr.append(str(numbers[1]))
        expr.append(brackets[1])
    else:
        expr.append(str(numbers[0]))
    
    expr.append(random.choice(ops))
    
    if random.random() > 0.5:
        expr.append(abs_symbol)
        expr.append('(')
        expr.append(str(numbers[2]))
        expr.append(random.choice(ops))
        expr.append(str(numbers[3]))
        expr.append(')')
    else:
        expr.append(str(numbers[2]))
    
    expr.append(random.choice(ops))
    expr.append(str(numbers[3]))
    
    # 计算正确答案
    try:
        # 替换符号为Python运算符
        expr_str = ''.join(expr).replace('×', '*').replace('÷', '/')
        # 处理绝对值符号
        expr_str = expr_str.replace('│', 'abs(').replace(')', '))')
        
        # 计算结果
        result = eval(expr_str)
        correct_answer = str(int(result))
    except:
        return generate(level, **kwargs)
    
    return {
        'question_text': '計算 `' + ''.join(expr) + '` 的值。',
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        return {
            'correct': str(int(user_answer)) == correct_answer,
            'result': '正確' if str(int(user_answer)) == correct_answer else '錯誤'
        }
    except:
        return {
            'correct': False,
            'result': '錯誤'
        }