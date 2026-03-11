denominator = v2 * v3 - v4

def check(user_answer, correct_answer):
    try:
        return {'correct': str(user_answer).strip() == str(correct_answer).strip(), 'result': '自動補全比對'}
    except:
        return {'correct': False, 'result': '錯誤'}

def generate():
    return {'question_text': 'Fallback due to severe hallucination', 'correct_answer': '\\text{Failed}'}