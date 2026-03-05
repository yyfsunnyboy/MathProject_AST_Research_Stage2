def generate():
    return {
        'question_text': '計算 $(-2 \\frac{3}{4}) + 1 \\frac{2}{7}$ 的值。',
        'answer': '',
        'correct_answer': '(-1\\frac{11}{28})',
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        ua = str(user_answer).strip()
        ca = str(correct_answer).strip()
        if ua == ca:
            return {'correct': True, 'result': '正確'}
        if Fraction(ua) == Fraction(ca):
            return {'correct': True, 'result': '正確'}
    except Exception:
        pass
    return {'correct': False, 'result': '錯誤'}