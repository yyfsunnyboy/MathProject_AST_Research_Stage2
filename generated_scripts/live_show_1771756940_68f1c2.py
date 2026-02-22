import random

def format_poly(coeffs):
    res = ""
    for i in range(len(coeffs) - 1, -1, -1):
        c = coeffs[i]
        if c == 0:
            continue
        s = ""
        if c > 0:
            if res != "":
                s = "+"
        else:
            s = "-"
        v = abs(c)
        if i == 0:
            t = str(v)
        elif i == 1:
            t = "x" if v == 1 else str(v) + "x"
        else:
            t = "x^" + str(i) if v == 1 else str(v) + "x^" + str(i)
        res += s + t
    return res if res != "" else "0"

def generate(level=1, **kwargs):
    op = random.choice(["+", "-", "*"])
    if op in ["+", "-"]:
        d1 = random.randint(1, 2)
        d2 = random.randint(1, 2)
        p1 = [random.randint(-10, 10) for _ in range(d1 + 1)]
        p2 = [random.randint(-10, 10) for _ in range(d2 + 1)]
        if all(x == 0 for x in p1): p1[0] = 1
        if all(x == 0 for x in p2): p2[0] = 1
        if op == "+":
            rlen = max(len(p1), len(p2))
            rc = [0] * rlen
            for i in range(rlen):
                v1 = p1[i] if i < len(p1) else 0
                v2 = p2[i] if i < len(p2) else 0
                rc[i] = v1 + v2
        else:
            rlen = max(len(p1), len(p2))
            rc = [0] * rlen
            for i in range(rlen):
                v1 = p1[i] if i < len(p1) else 0
                v2 = p2[i] if i < len(p2) else 0
                rc[i] = v1 - v2
    else:
        p1 = [random.randint(-5, 5) for _ in range(2)]
        p2 = [random.randint(-5, 5) for _ in range(2)]
        if all(x == 0 for x in p1): p1[0] = 1
        if all(x == 0 for x in p2): p2[0] = 1
        rc = [0] * (len(p1) + len(p2) - 1)
        for i in range(len(p1)):
            for j in range(len(p2)):
                rc[i+j] += p1[i] * p2[j]
    q1 = format_poly(p1)
    q2 = format_poly(p2)
    op_sym = op if op != "*" else "\\times"
    txt = f"Calculate $({q1}){op_sym}({q2})$"
    return {
        'question_text': txt,
        'answer': '',
        'correct_answer': format_poly(rc),
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}