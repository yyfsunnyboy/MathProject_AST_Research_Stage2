import random

def generate(level=1, **kwargs):
    while True:
        a = random.randint(-50, 50)
        b = random.randint(-50, 50)
        op = random.choice(['+', '-'])
        if op == '+':
            x = a + b
        else:
            x = a - b
        if x != 0:
            break

    def get_divisor(x):
        while True:
            c = random.randint(-abs(x), abs(x))
            if c != 0 and x % c == 0:
                return c
    c = get_divisor(x)

    d = random.randint(-50, 50)
    e = random.randint(-50, 50)
    f = random.randint(-50, 50)
    g = random.randint(-50, 50)

    question_text = f"[({a}{op}{b})]÷{c}×{d}+|{e}×{f}-{g}|"
    part1 = (x // c) * d
    part2 = abs(e * f - g)
    correct_answer = part1 + part2

    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': str(correct_answer),
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        user = int(user_answer)
        correct = int(correct_answer)
        return {
            'correct': user == correct,
            'result': '正確' if user == correct else '錯誤'
        }
    except ValueError:
        return {'correct': False, 'result': '錯誤'}