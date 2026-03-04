def generate(level=1, **kwargs):
    return {'question_text': '9\\frac{1}{5}\\times 239+9\\frac{1}{5}\\times (-39)', 'answer': '', 'correct_answer': '9\\frac{1}{5}\\times 200', 'mode': 1}

def check(user_answer, correct_answer):
    try:
        return {'correct': str(user_answer).strip() == str(correct_answer).strip(), 'result': '自動補全比對'}
    except:
        return {'correct': False, 'result': '錯誤'}