import random

def generate(level=1, **kwargs):
    ops = ['+', '-', '÷', '×']
    abs_pos = random.choice([0, 1, 2])
    expr = []
    nums = []
    
    # 生成括号内的表达式
    a = random.randint(1, 10*level)
    b = random.randint(1, 10*level)
    op1 = random.choice(['+', '-'])
    expr.append(f'({random.choice([-1,1])}{a}{op1}{random.choice([-1,1])}{b})')
    nums.extend([a, b])
    
    # 生成除法和乘法部分
    c = random.randint(1, 10*level)
    d = random.randint(1, 10*level)
    expr.append(f'÷{c}×{d}')
    nums.extend([c, d])
    
    # 生成绝对值部分
    e = random.randint(1, 10*level)
    f = random.randint(1, 10*level)
    g = random.randint(1, 10*level)
    op2 = random.choice(['×', '-'])
    abs_expr = f'|{e}{op2}{f}{random.choice(['×', '-'])}{g}|'
    expr.append(abs_expr)
    nums.extend([e, f, g])
    
    # 组合完整表达式
    question = ' '.join(expr)
    
    # 计算正确答案
    try:
        # 将运算符转换为Python表达式
        py_expr = question.replace('÷', '/').replace('×', '*')
        # 处理负号
        py_expr = py_expr.replace('(-', '( -').replace(')-', ') -')
        correct_answer = str(int(eval(py_expr)))
    except:
        return generate(level=level)
    
    return {
        'question_text': f'計算 `{question}` 的值。',
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        return {
            'correct': int(user_answer.strip()) == int(correct_answer),
            'result': '正確' if int(user_answer.strip()) == int(correct_answer) else '錯誤'
        }
    except:
        return {
            'correct': False,
            'result': '錯誤'
        }