import random

def generate(level=1, **kwargs):
    if level == 1:
        c = random.randint(1, 5)
        k = random.randint(-5, 5)
        target_sum = c * k
        while True:
            a = random.randint(-20, 20)
            b = target_sum - a
            if -20 <= b <= 20:
                break
        d = random.randint(1, 5)
        e = random.randint(-10, 10)
        f = random.randint(-10, 10)
        g = random.randint(-10, 10)
        abs_part = abs(e * f - g)
        question = f"({a}+{b})÷{c}×{d}+|{e}×{f}-{g}|"
        correct_answer = (target_sum // c) * d + abs_part
        return {
            'question_text': question,
            'answer': '',
            'correct_answer': str(correct_answer),
            'mode': 1
        }
    else:
        return {
            'question_text': '',
            'answer': '',
            'correct_answer': '',
            'mode': 1
        }

def check(user_answer, correct_answer):
    user_answer = user_answer.strip()
    return {
        'correct': user_answer == correct_answer,
        'result': '正確' if user_answer == correct_answer else '錯誤'
    }