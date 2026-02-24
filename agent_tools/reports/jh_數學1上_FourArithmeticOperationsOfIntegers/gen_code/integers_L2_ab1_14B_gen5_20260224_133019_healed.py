import random

def generate(level=1, **kwargs):
    question = []
    operations = ['+', '-', '×', '÷']
    num_operators = random.randint(3, 5)
    num_terms = num_operators + 1
    numbers = []
    signs = ['+', '-']
    
    for _ in range(num_terms):
        if level == 1:
            numbers.append(random.randint(-50, 50))
        elif level == 2:
            numbers.append(random.randint(-100, 100))
        else:
            numbers.append(random.randint(-200, 200))
    
    for i in range(num_operators):
        if i == 0:
            question.append(str(numbers[i]))
        else:
            question.append(operations[random.randint(0, 3)])
            question.append(str(numbers[i]))
    
    if random.random() < 0.3:
        question.insert(random.randint(1, len(question)-1), '|')
        question.insert(random.randint(1, len(question)-1), '|')
    
    question_text = ''.join(question)
    correct_answer = eval(question_text.replace('×', '*').replace('÷', '/'))
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': str(correct_answer),
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        user_answer = int(user_answer)
        correct_answer = int(correct_answer)
        correct = user_answer == correct_answer
        result = '正確' if correct else '錯誤'
        return {'correct': correct, 'result': result}
    except:
        return {'correct': False, 'result': '錯誤'}