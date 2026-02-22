import random

def format_poly(coeffs):
    res = ""
    first = True
    for i in range(len(coeffs) - 1, -1, -1):
        c = coeffs[i]
        if c == 0:
            continue
        if c > 0:
            if not first:
                res += "+"
        else:
            res += "-"
        abs_c = abs(c)
        if abs_c != 1 or i == 0:
            res += str(abs_c)
        if i > 0:
            res += "x"
            if i > 1:
                res += "^" + str(i)
        first = False
    return res if res else "0"

def generate(level=1, **kwargs):
    if level == 1:
        op = random.randint(1, 4)
    elif level == 2:
        op = 3
    elif level == 3:
        op = 4
    else:
        op = random.randint(1, 4)
    if op == 1:
        p1 = [random.randint(-9, 9) for _ in range(3)]
        p2 = [random.randint(-9, 9) for _ in range(3)]
        ans = [p1[i] + p2[i] for i in range(3)]
        q = "(" + format_poly(p1) + ") + (" + format_poly(p2) + ")"
        correct = format_poly(ans)
    elif op == 2:
        if random.random() > 0.5:
            p1 = [random.randint(-9, 9) for _ in range(3)]
            p2 = [random.randint(-9, 9) for _ in range(3)]
            p3 = [random.randint(-9, 9) for _ in range(3)]
            ans = [p1[i] - (p2[i] - p3[i]) for i in range(3)]
            q = "(" + format_poly(p1) + ") - [(" + format_poly(p2) + ") - (" + format_poly(p3) + ")]"
        else:
            p1 = [random.randint(-9, 9) for _ in range(3)]
            p2 = [random.randint(-9, 9) for _ in range(3)]
            ans = [p1[i] - p2[i] for i in range(3)]
            q = "(" + format_poly(p1) + ") - (" + format_poly(p2) + ")"
        correct = format_poly(ans)
    elif op == 3:
        p1 = [random.randint(-5, 5) for _ in range(2)]
        p2 = [random.randint(-5, 5) for _ in range(2)]
        ans = [0] * 3
        for i in range(2):
            for j in range(2):
                ans[i+j] += p1[i] * p2[j]
        q = "(" + format_poly(p1) + ")(" + format_poly(p2) + ")"
        correct = format_poly(ans)
    else:
        k = random.randint(-5, 5)
        a = random.choice([-3, -2, -1, 1, 2, 3])
        b = random.randint(-5, 5)
        p_quot = [b, a]
        rem = random.randint(-5, 5)
        p_num = [b*(-k) + rem, a*(-k) + b, a]
        p_div = [-k, 1]
        q = "(" + format_poly(p_num) + ") \\div (" + format_poly(p_div) + ")"
        correct = "Q: " + format_poly(p_quot) + ", R: " + str(rem)
    return {
        'question_text': "Simplify $" + q + "$",
        'answer': '',
        'correct_answer': correct,
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}