# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 38.67s | Tokens: In=624, Out=993
# Created At: 2026-02-23 00:38:59
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
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