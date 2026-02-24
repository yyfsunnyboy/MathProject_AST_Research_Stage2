import random

def generate(level=1, **kwargs):
    question = []
    operations = ['+', '-', '*', '//']
    numbers = []
    signs = ['+', '-']
    
    if level == 1:
        num_range = (1, 20)
    else:
        num_range = (10, 100)
    
    for _ in range(3):
        num = random.randint(*num_range)
        sign = random.choice(signs)
        numbers.append(f"{sign}{num}")
    
    random.shuffle(numbers)
    ops = random.choices(operations, k=2)
    
    question.append(f"({numbers[0]}){ops[0]}({numbers[1]}){ops[1]}({numbers[2]})")
    
    # Add absolute value part
    abs_num1 = random.randint(1, 10)
    abs_num2 = random.randint(1, 10)
    abs_sign = random.choice(signs)
    abs_expr = f"|{abs_sign}{abs_num1}*({abs_sign}{abs_num2})-{random.randint(1, 10)}|"
    question.append(abs_expr)
    
    question_text = "計算 `" + "÷".join(question) + "` 的值。"
    
    # Calculate correct answer
    try:
        expr = question[0].replace('//', '/')
        expr += f" / {abs_num2} * {abs_num1} - {random.randint(1, 10)}"
        correct_answer = eval(expr)
    except:
        correct_answer = 0
    
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
        correct_flag = user == correct
    except:
        correct_flag = False
    
    return {
        'correct': correct_flag,
        'result': '正確' if correct_flag else '錯誤'
    }