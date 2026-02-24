import random
import math

def generate(level=1, **kwargs):
    question = []
    operators = ['+', '-', '*', '//']
    numbers = []
    parentheses = 0
    abs_used = False

    if level == 1:
        num_range = (1, 20)
    elif level == 2:
        num_range = (10, 50)
    elif level == 3:
        num_range = (20, 100)

    for _ in range(4):
        if random.random() < 0.3:
            num = random.randint(*num_range)
            numbers.append(num if random.random() > 0.5 else -num)
        else:
            num = random.randint(*num_range)
            numbers.append(num if random.random() > 0.5 else -num)

    for i in range(3):
        if random.random() < 0.3:
            question.append(str(numbers[i]))
            if i < 2:
                question.append(random.choice(operators))
        else:
            if random.random() < 0.2:
                question.append(f"({numbers[i]})")
                parentheses += 1
            else:
                question.append(str(numbers[i]))
            if i < 2:
                question.append(random.choice(operators))

    if parentheses == 0 and random.random() < 0.4:
        question.insert(0, '(')
        question.append(')')
        parentheses += 1

    if random.random() < 0.3:
        abs_used = True
        abs_pos = random.randint(0, len(question) - 1)
        question.insert(abs_pos, '|')
        question.insert(abs_pos + 1, '|')

    question_text = ''.join(question)
    try:
        correct_answer = eval(question_text)
        if not isinstance(correct_answer, int):
            correct_answer = int(correct_answer)
    except:
        correct_answer = "0"

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
        return {
            'correct': user == correct,
            'result': '正確' if user == correct else '錯誤'
        }
    except:
        return {
            'correct': False,
            'result': '錯誤'
        }