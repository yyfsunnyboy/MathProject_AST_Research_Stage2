import random

def generate(level=1, **kwargs):
    a = random.randint(-20, 20)
    b = random.randint(-20, 20)
    sum_ab = a + b
    possible_c = [i for i in range(1, 11) if sum_ab % i == 0]
    c = random.choice(possible_c)
    d = random.randint(1, 10)
    e = random.randint(-20, 20)
    f = random.randint(-20, 20)
    g = random.randint(-20, 20)
    expr = f"(({a} + {b}) ÷ {c}) × {d} + |{e} × {f} - {g}|"
    part1 = (sum_ab // c) * d
    part2 = abs(e * f - g)
    correct_answer = part1 + part2
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
    except ValueError:
        return {'correct': False, 'result': '錯誤'}