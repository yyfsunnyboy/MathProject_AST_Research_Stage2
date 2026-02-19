import random
from fractions import Fraction

def generate(level=1, **kwargs):
    a = random.randint(-10, 10)
    b = random.randint(-10, 10)
    c = random.randint(-10, 10)
    d = random.randint(1, 10)
    e = random.choice([x for x in range(-10, 11) if x != 0])
    f = random.randint(1, 10)
    g = random.randint(-10, 10)
    h = random.randint(-10, 10)
    i = random.randint(1, 10)
    j = random.randint(-10, 10)
    question_text = f"[({a}+{b})×{c}/{d}]÷({e}/{f}) + |{g}×{h}/{i}-{j}|"
    python_expr = f"((({a} + {b}) * {c}/{d}) / ({e}/{f})) + abs({g} * {h}/{i} - {j})"
    try:
        result = eval(python_expr)
        correct_answer = str(Fraction(result).limit_denominator())
    except:
        correct_answer = "0"
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    user_answers = [a.strip() for a in user_answer.split(',')] if ',' in user_answer else [user_answer.strip()]
    correct_answers = [a.strip() for a in correct_answer.split(',')] if ',' in correct_answer else [correct_answer.strip()]
    for ua in user_answers:
        try:
            user_fraction = Fraction(ua)
            for ca in correct_answers:
                try:
                    correct_fraction = Fraction(ca)
                    if user_fraction == correct_fraction:
                        return {'correct': True, 'result': '正確'}
                except:
                    pass
        except:
            pass
    return {'correct': False, 'result': '錯誤'}