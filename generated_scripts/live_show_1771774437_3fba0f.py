import random

def generate(level=1, **kwargs):
    def fmt(n):
        return "(" + str(n) + ")" if n < 0 else str(n)
    
    limit = 20 + (level * 30)
    op = random.choice(['+', '-', '*', '/'])
    
    if op == '+':
        a = random.randint(-limit, limit)
        b = random.randint(-limit, limit)
        res = a + b
        sym = '+'
    elif op == '-':
        a = random.randint(-limit, limit)
        b = random.randint(-limit, limit)
        res = a - b
        sym = '-'
    elif op == '*':
        a = random.randint(-12, 12)
        b = random.randint(-12, 12)
        res = a * b
        sym = '×'
    else:
        b = random.choice([i for i in range(-12, 13) if i != 0])
        res = random.randint(-12, 12)
        a = b * res
        sym = '÷'
        
    return {
        'question_text': fmt(a) + sym + fmt(b),
        'answer': '',
        'correct_answer': str(res),
        'mode': 1
    }

def check(user_answer, correct_answer):
    is_correct = str(user_answer).strip() == str(correct_answer).strip()
    return {
        'correct': is_correct,
        'result': '正確' if is_correct else '錯誤'
    }