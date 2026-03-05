return {'question_text': question_text, 'answer': '', 'correct_answer': str(int(ans)), 'mode': 1}

def check(user_answer, correct_answer):
    try:
        if str(user_answer).strip() == str(correct_answer).strip():
            return {'correct': True, 'result': '正確'}
        if abs(float(user_answer) - float(correct_answer)) < 1e-06:
            return {'correct': True, 'result': '正確'}
    except:
        pass
    return {'correct': False, 'result': '錯誤'}

def generate():
    return {'question_text': 'Fallback due to severe hallucination', 'correct_answer': '\\text{Failed}'}