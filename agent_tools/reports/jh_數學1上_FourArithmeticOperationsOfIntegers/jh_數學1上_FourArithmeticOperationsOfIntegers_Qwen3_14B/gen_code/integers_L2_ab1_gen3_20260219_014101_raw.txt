import random

def generate(level=1, **kwargs):
    ops = ['+', '-', '×', '÷']
    abs_expr = f"|{random.randint(1,10)}×({random.randint(-10,10)}-{random.randint(1,10)})|"
    bracket_expr = f"[({random.randint(-20,20)}{random.choice(ops)}{random.randint(-20,20)})]{random.choice(['÷', '×'])}{random.randint(1,10)}"
    question = f"{bracket_expr}+{abs_expr}"
    try:
        correct = str(eval(question.replace('×','*').replace('÷','//')))
    except:
        correct = str(eval(question.replace('×','*').replace('÷','/')))
    return {
        'question_text': question,
        'answer': '',
        'correct_answer': correct,
        'mode': 1
    }

def check(user_answer, correct_answer):
    return {
        'correct': user_answer == correct_answer,
        'result': '正確' if user_answer == correct_answer else '錯誤'
    }