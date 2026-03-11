def generate():
    import random
    v1 = random_positive(1, 100)
    v2 = random_negative(-100, -1)
    v3 = random_positive(1, 10)
    v4 = random_positive(1, 15)
    v5 = random_negative(-15, -1)
    numerator = abs(v1 * v2 - v3) * v5
    denominator = v4

def check(user_answer, correct_answer):
    try:
        return {'correct': str(user_answer).strip() == str(correct_answer).strip(), 'result': '自動補全比對'}
    except:
        return {'correct': False, 'result': '錯誤'}