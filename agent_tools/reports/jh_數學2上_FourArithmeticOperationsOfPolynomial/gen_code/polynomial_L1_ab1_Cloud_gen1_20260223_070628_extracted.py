import random

def poly_to_latex(coeffs):
    res = ""
    for i in range(len(coeffs) - 1, -1, -1):
        c = coeffs[i]
        if c == 0:
            continue
        s = "+" if c > 0 and res else ""
        if i == 0:
            res += s + str(c)
        elif i == 1:
            if c == 1:
                res += s + "x"
            elif c == -1:
                res += "-x"
            else:
                res += s + str(c) + "x"
        else:
            if c == 1:
                res += s + "x^{" + str(i) + "}"
            elif c == -1:
                res += "-x^{" + str(i) + "}"
            else:
                res += s + str(c) + "x^{" + str(i) + "}"
    return res if res else "0"

def poly_to_str(coeffs):
    res = ""
    for i in range(len(coeffs) - 1, -1, -1):
        c = coeffs[i]
        if c == 0:
            continue
        s = "+" if c > 0 and res else ""
        if i == 0:
            res += s + str(c)
        elif i == 1:
            if c == 1:
                res += s + "x"
            elif c == -1:
                res += "-x"
            else:
                res += s + str(c) + "x"
        else:
            if c == 1:
                res += s + "x^" + str(i)
            elif c == -1:
                res += "-x^" + str(i)
            else:
                res += s + str(c) + "x^" + str(i)
    return res if res else "0"

def generate(level=1, **kwargs):
    if level == 1:
        op = random.choice(["+", "-"])
        d1 = random.randint(1, 2)
        d2 = random.randint(1, 2)
        p1 = [random.randint(-5, 5) for _ in range(d1 + 1)]
        p2 = [random.randint(-5, 5) for _ in range(d2 + 1)]
        while p1[-1] == 0:
            p1[-1] = random.randint(-5, 5)
        while p2[-1] == 0:
            p2[-1] = random.randint(-5, 5)
        
        max_d = max(len(p1), len(p2))
        p1_pad = p1 + [0] * (max_d - len(p1))
        p2_pad = p2 + [0] * (max_d - len(p2))
        
        if op == "+":
            res_coeffs = [p1_pad[i] + p2_pad[i] for i in range(max_d)]
        else:
            res_coeffs = [p1_pad[i] - p2_pad[i] for i in range(max_d)]
        
        question_text = f"計算 $({poly_to_latex(p1)}) {op} ({poly_to_latex(p2)})$"
    else:
        d1 = 1
        d2 = random.randint(1, 2)
        p1 = [random.randint(-3, 3) for _ in range(d1 + 1)]
        p2 = [random.randint(-3, 3) for _ in range(d2 + 1)]
        while p1[-1] == 0:
            p1[-1] = random.randint(-3, 3)
        while p2[-1] == 0:
            p2[-1] = random.randint(-3, 3)
        
        res_coeffs = [0] * (len(p1) + len(p2) - 1)
        for i in range(len(p1)):
            for j in range(len(p2)):
                res_coeffs[i + j] += p1[i] * p2[j]
        
        question_text = f"展開並化簡 $({poly_to_latex(p1)})({poly_to_latex(p2)})$"

    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': poly_to_str(res_coeffs),
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}