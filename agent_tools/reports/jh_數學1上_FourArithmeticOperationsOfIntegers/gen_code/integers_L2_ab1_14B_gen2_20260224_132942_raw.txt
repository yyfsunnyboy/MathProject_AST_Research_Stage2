import random

def generate(level=1, **kwargs):
    question = []
    operations = ['+', '-', '*', '//']
    numbers = []
    signs = ['+', '-']
    
    if level == 1:
        num_range = (1, 20)
    elif level == 2:
        num_range = (10, 50)
    else:
        num_range = (50, 100)
    
    for _ in range(4):
        num = random.randint(*num_range)
        sign = random.choice(signs)
        numbers.append(f"{sign}{num}")
    
    for i in range(3):
        op = random.choice(operations)
        question.append(numbers[i])
        question.append(op)
    question.append(numbers[3])
    
    question_text = "計算 `" + " ".join(question) + "` 的值。"
    correct_answer = eval(" ".join(question))
    
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': str(correct_answer),
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        correct = user_answer.strip() == correct_answer
    except:
        correct = False
    
    return {
        'correct': correct,
        'result': '正確' if correct else '錯誤'
    }