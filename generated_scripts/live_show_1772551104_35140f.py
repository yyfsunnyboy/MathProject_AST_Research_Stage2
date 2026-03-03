import random

def generate(level=1, **kwargs):
    def f(n):
        return f"({n})" if n < 0 else str(n)
    def get_p():
        if random.random() < 0.5:
            b = random.choice([i for i in range(-15, 16) if i != 0])
            r = random.randint(-15, 15)
            return r, f"{f(b*r)} \\div {f(b)}"
        else:
            a = random.randint(-12, 12)
            b = random.randint(-12, 12)
            return a * b, f"{f(a)} \\times {f(b)}"
    v, txt = get_p()
    for _ in range(level):
        op = random.choice(['+', '-'])
        v2, s2 = get_p()
        if op == '+':
            v += v2
        else:
            v -= v2
        txt += f" {op} {s2}"
    return {
        'question_text': txt,
        'answer': '',
        'correct_answer': str(v),
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        c = int(user_answer) == int(correct_answer)
    except:
        c = False
    return {'correct': c, 'result': '正確' if c else '錯誤'}