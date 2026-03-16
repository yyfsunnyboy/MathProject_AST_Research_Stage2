pattern_id = 'p2a_mult_direct'
difficulty = 'mid'
term_count = 2

def check(user_answer, correct_answer):
    try:
        return {'correct': str(user_answer).strip() == str(correct_answer).strip(), 'result': '自動補全比對'}
    except:
        return {'correct': False, 'result': '錯誤'}

def generate(level=1, **kwargs):
    return {'question_text': 'Fallback due to missing generate() wrapper', 'correct_answer': '\\text{Failed}'}