import random

def generate(level=1, **kwargs):
    def f(n):
        return f"( -{abs(n)} )" if n < 0 else str(n)
    t = random.randint(1, 4)
    if t == 1:
        c = random.choice([i for i in range(-12, 13) if i != 0])
        res_div = random.randint(-10, 10)
        sum_ab = res_div * c
        a = random.randint(-30, 30)
        b = sum_ab - a
        d = random.randint(-10, 10)
        txt = f"[ {f(a)} + {f(b)} ] ÷ {f(c)} × {f(d)}"
        ans = res_div * d
    elif t == 2:
        d = random.choice([i for i in range(-10, 11) if i != 0])
        res_div = random.randint(-10, 10)
        c = res_div * d
        a = random.randint(-15, 15)
        b = random.randint(-15, 15)
        txt = f"{f(a)} × {f(b)} + {f(c)} ÷ {f(d)}"
        ans = (a * b) + res_div
    elif t == 3:
        c = random.randint(-15, 15)
        d = random.randint(-15, 15)
        b = random.randint(-10, 10)
        a = random.randint(-50, 50)
        txt = f"{f(a)} - [ {f(b)} × ( {f(c)} + {f(d)} ) ]"
        ans = a - (b * (c + d))
    else:
        a = random.randint(-20, 20)
        b = random.randint(-10, 10)
        c = random.randint(-10, 10)
        d = random.randint(-20, 20)
        txt = f"{f(a)} × {f(b)} - {f(c)} × {f(d)}"
        ans = (a * b) - (c * d)
    return {
        'question_text': f"計算 {txt} 的值。",
        'answer': '',
        'correct_answer': str(ans),
        'mode': 1
    }

def check(user_answer, correct_answer):
    res = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': res, 'result': '正確' if res else '錯誤'}