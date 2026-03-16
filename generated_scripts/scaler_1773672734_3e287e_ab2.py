def generate():
    return {
        'question_text': '',
        'answer': '',
        'correct_answer': '',
        'solution_steps': [],
        'mode': 1,
        '_o1_healed': False
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}