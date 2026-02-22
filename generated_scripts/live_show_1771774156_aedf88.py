import random

def format_poly(coeffs):
    res = ""
    for i in range(len(coeffs) - 1, -1, -1):
        c = coeffs[i]
        if c == 0:
            continue
        if c > 0:
            part = "+" if res != "" else ""
        else:
            part = "-"
        val = abs(c)
        if i == 0:
            part += str(val)
        elif i == 1:
            part += (str(val) if val != 1 else "") + "x"
        else:
            part += (str(val) if val != 1 else "") + "x^" + str(i)
        res += part
    return res if res != "" else "0"

def generate(level=1, **kwargs):
    if level == 1:
        p1 = [random.randint(-10, 10) for _ in range(3)]
        p2 = [random.randint(-10, 10) for _ in range(3)]
        p3 = [random.randint(-10, 10) for _ in range(3)]
        for p in [p1, p2, p3]:
            if all(v == 0 for v in p):
                p[0] = random.randint(1, 10)
        op1 = random.choice(['+', '-'])
        op2 = random.choice(['+', '-'])
        res = [0] * 3
        for i in range(3):
            v = p1[i]
            if op1 == '+': v += p2[i]
            else: v -= p2[i]
            if op2 == '+': v += p3[i]
            else: v -= p3[i]
            res[i] = v
        q = "(" + format_poly(p1) + ")" + op1 + "(" + format_poly(p2) + ")" + op2 + "(" + format_poly(p3) + ")"
        ans = format_poly(res)
    else:
        p1 = [random.randint(-5, 5) for _ in range(2)]
        p2 = [random.randint(-5, 5) for _ in range(2)]
        for p in [p1, p2]:
            if all(v == 0 for v in p):
                p[0] = random.randint(1, 5)
        res = [0] * 3
        for i in range(2):
            for j in range(2):
                res[i+j] += p1[i] * p2[j]
        q = "(" + format_poly(p1) + ")(" + format_poly(p2) + ")"
        ans = format_poly(res)
    return {
        'question_text': "Simplify $" + q + "$",
        'answer': '',
        'correct_answer': ans,
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}