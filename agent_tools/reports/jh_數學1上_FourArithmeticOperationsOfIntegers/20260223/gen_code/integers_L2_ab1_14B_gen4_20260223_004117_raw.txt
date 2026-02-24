import random

def generate(level=1, **kwargs):
    ops = ['+', '-', '÷', '×']
    num_range = [(-50, 50), (-100, 100)][level-1]
    a = random.randint(*num_range)
    b = random.randint(*num_range)
    c = random.randint(*num_range)
    d = random.randint(*num_range)
    e = random.randint(*num_range)
    f = random.randint(*num_range)
    
    part1 = f"({a}{ops[0]}{b})"
    part2 = f"{c}{ops[1]}{d}"
    part3 = f"{e}{ops[2]}{f}"
    
    question = f"{part1}{ops[3]}{part2}×{part3}+|{part3}|"
    question = question.replace('÷', '/').replace('×', '*')
    
    try:
        correct_answer = eval(question)
        if not isinstance(correct_answer, int):
            raise ValueError
    except:
        return generate(level, **kwargs)
    
    return {
        'question_text': question.replace('/', '÷').replace('*', '×'),
        'answer': '',
        'correct_answer': str(int(correct_answer)),
        'mode': 1
    }

def check(user_answer, correct_answer):
    return {
        'correct': user_answer == correct_answer,
        'result': '正確' if user_answer == correct_answer else '錯誤'
    }