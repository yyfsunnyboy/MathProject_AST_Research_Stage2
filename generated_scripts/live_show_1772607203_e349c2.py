def generate(level=1, **kwargs):
    return {'question_text': '3\\frac{9}{11}\\times(-57)-1\\frac{9}{11}\\times(-57)', 'answer': '', 'correct_answer': '2\\times(-57)', 'mode': 1}

def check(user_answer, correct_answer):
    try:
        return {'correct': str(user_answer).strip() == str(correct_answer).strip(), 'result': '自動補全比對'}
    except:
        return {'correct': False, 'result': '錯誤'}