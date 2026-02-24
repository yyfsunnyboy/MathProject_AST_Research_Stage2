import random

def generate(level=1, **kwargs):
    question = []
    operations = ['+', '-', '×', '÷']
    num_operands = random.randint(3, 5)
    operands = []
    for _ in range(num_operands):
        if level == 1:
            operands.append(random.randint(-50, 50))
        elif level == 2:
            operands.append(random.randint(-100, 100))
        else:
            operands.append(random.randint(-200, 200))
    
    ops = random.choices(operations, k=num_operands - 1)
    
    for i in range(num_operands):
        if i > 0:
            question.append(ops[i - 1])
        if isinstance(operands[i], int) and operands[i] < 0:
            question.append(f'({operands[i]})')
        else:
            question.append(str(operands[i]))
    
    question_text = ''.join(question)
    
    # Calculate correct answer
    expression = question_text.replace('×', '*').replace('÷', '/')
    try:
        correct_answer = eval(expression)
    except ZeroDivisionError:
        return generate(level=level)
    
    if not isinstance(correct_answer, int):
        return generate(level=level)
    
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': str(correct_answer),
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        user = int(user_answer)
        correct = int(correct_answer)
        correct_bool = user == correct
    except:
        correct_bool = False
    
    return {
        'correct': correct_bool,
        'result': '正確' if correct_bool else '錯誤'
    }