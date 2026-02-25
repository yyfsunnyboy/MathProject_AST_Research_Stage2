import random

def generate(level=1, **kwargs):
    def f(n):
        return f"({n})" if n < 0 else str(n)
    if level == 1:
        a = random.randint(-100, 100)
        b = random.randint(-100, 100)
        if random.random() > 0.5:
            ans = a + b
            question_text = f"計算 $${f(a)} + {f(b)}$$ 的值。"
        else:
            ans = a - b
            question_text = f"計算 $${f(a)} - {f(b)}$$ 的值。"
    elif level == 2:
        mode = random.choice(['mul', 'div'])
        if mode == 'mul':
            a = random.randint(-20, 20)
            b = random.randint(-20, 20)
            ans = a * b
            question_text = f"計算 $${f(a)} \\times {f(b)}$$ 的值。"
        else:
            b = random.choice([i for i in range(-20, 21) if i != 0])
            ans = random.randint(-20, 20)
            a = ans * b
            question_text = f"計算 $${f(a)} \\div {f(b)}$$ 的值。"
    else:
        v1 = random.randint(900, 999)
        v3 = random.choice([i for i in range(-10, 11) if i not in [-1, 0, 1]])
        v2 = 1000 - v1
        ans = v1 * v3 + v2 * v3
        question_text = f"計算 $${f(v1)} \\times {f(v3)} + {f(v2)} \\times {f(v3)}$$ 的值。"
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': str(ans),
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        ua = str(user_answer).strip()
        ca = str(correct_answer).strip()
        is_correct = (ua == ca)
    except:
        is_correct = False
    return {
        'correct': is_correct,
        'result': '正確' if is_correct else '錯誤'
    }