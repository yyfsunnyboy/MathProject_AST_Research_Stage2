import random

def generate(level=1, **kwargs):
    if level == 1:
        range_min = -10
        range_max = 10
    else:
        range_min = -100
        range_max = 100

    a = random.randint(range_min, range_max)
    b = random.randint(range_min, range_max)
    sum_ab = a + b

    while True:
        if sum_ab != 0:
            c = random.randint(1, abs(sum_ab))
        else:
            c = random.randint(1, 10)
        if c != 0 and (sum_ab % c == 0 or sum_ab == 0):
            break

    d = random.randint(range_min, range_max)

    e = random.randint(range_min, range_max)
    f = random.randint(range_min, range_max)
    g = random.randint(range_min, range_max)

    expr = f"(({a} + {b}) ÷ {c}) × {d} + |{e} × {f} - {g}|"

    part1 = (a + b) // c
    part2 = part1 * d
    part3 = e * f - g
    part4 = abs(part3)
    correct_answer = part2 + part4

    return {
        'question_text': expr,
        'answer': '',
        'correct_answer': str(correct_answer),
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        user_num = int(user_answer)
        correct_num = int(correct_answer)
        return {'correct': user_num == correct_num, 'result': '正確' if user_num == correct_num else '錯誤'}
    except:
        return {'correct': False, 'result': '錯誤'}