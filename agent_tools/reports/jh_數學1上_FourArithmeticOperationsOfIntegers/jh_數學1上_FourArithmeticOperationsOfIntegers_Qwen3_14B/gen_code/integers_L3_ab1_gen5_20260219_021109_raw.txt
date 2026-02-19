import random

def generate(level=1, **kwargs):
    ops = ['+', '-', '×', '÷']
    brackets = ['(', ')']
    abs_symbol = '│'
    
    # 生成括号内部分
    bracket_part = f"{random.randint(-50, -10)}{random.choice(ops)}{random.randint(-50, -10)}"
    
    # 生成除法和乘法部分
    while True:
        a = random.randint(1, 20)
        b = random.randint(1, 20)
        if a % b == 0:
            division_part = f"{a}÷{b}"
            break
    
    # 生成绝对值部分
    while True:
        c = random.randint(1, 10)
        d = random.randint(1, 10)
        e = random.randint(1, 10)
        if (c * d - e) != 0:
            abs_part = f"{abs_symbol}{c}×({d})-{e}{abs_symbol}"
            break
    
    # 组合完整题目
    question = f"計算 $[{bracket_part}]×{division_part}+{abs_part}$ 的值。"
    
    # 计算正确答案
    bracket_val = eval(bracket_part.replace('×', '*').replace('÷', '/'))
    division_val = eval(division_part.replace('×', '*').replace('÷', '/'))
    abs_val = eval(abs_part.replace('×', '*').replace('÷', '/').replace('│', 'abs'))
    correct_answer = bracket_val * division_val + abs_val
    
    return {
        'question_text': question,
        'answer': '',
        'correct_answer': str(int(correct_answer)),
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