import random
from fractions import Fraction

def generate(level=1, **kwargs):
    a = random.randint(-5, 5)
    b = random.randint(-5, 5)
    c = random.randint(1, 5)
    d = random.randint(1, 5)
    e = random.randint(1, 5)
    f = random.randint(1, 5)
    g = random.randint(1, 5)
    h_num = random.randint(-5, 5)
    h_den = random.randint(1, 5)
    i = random.randint(1, 5)
    
    question_text = f"[({a}+{b})×{c}/{d}]÷({e}/{f}) + |{g}×({h_num}/{h_den})-{i}|"
    
    part1 = Fraction(a + b) * Fraction(c, d) * Fraction(f, e)
    part2 = abs(Fraction(g * h_num, h_den) - i)
    total = part1 + part2
    
    if total.denominator == 1:
        correct_answer = str(total.numerator)
    else:
        correct_answer = f"{total.numerator}/{total.denominator}"
    
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        if '/' in user_answer:
            num, den = user_answer.split('/')
            num = int(num)
            den = int(den)
            if den < 0:
                num *= -1
                den *= -1
            user_fraction = Fraction(num, den)
        else:
            user_fraction = Fraction(int(user_answer))
        
        if '/' in correct_answer:
            num, den = correct_answer.split('/')
            num = int(num)
            den = int(den)
            if den < 0:
                num *= -1
                den *= -1
            correct_fraction = Fraction(num, den)
        else:
            correct_fraction = Fraction(int(correct_answer))
        
        return {'correct': user_fraction == correct_fraction, 'result': '正確' if user_fraction == correct_fraction else '錯誤'}
    except:
        return {'correct': False, 'result': '錯誤'}