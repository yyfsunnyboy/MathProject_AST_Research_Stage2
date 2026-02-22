import random

def poly_to_str(coeffs):
    if not coeffs:
        return "0"
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
        if i == 0:
            res += str(abs_c)
        else:
            if abs_c != 1:
                res += str(abs_c)
            res += "x"
            if i > 1:
                res += "^" + str(i)
        first = False
    return res if res else "0"

def generate(level=1, **kwargs):
    ops = ['+', '-', '*']
    op = random.choice(ops)
    d1 = random.randint(1, level + 1)
    d2 = random.randint(1, level)
    p1 = [random.randint(-5, 5) for _ in range(d1 + 1)]
    p2 = [random.randint(-5, 5) for _ in range(d2 + 1)]
    while all(c == 0 for c in p1):
        p1 = [random.randint(-5, 5) for _ in range(d1 + 1)]
    while all(c == 0 for c in p2):
        p2 = [random.randint(-5, 5) for _ in range(d2 + 1)]
    s1 = poly_to_str(p1)
    s2 = poly_to_str(p2)
    if op == '+':
        max_len = max(len(p1), len(p2))
        res = [0] * max_len
        for i in range(max_len):
            v1 = p1[i] if i < len(p1) else 0
            v2 = p2[i] if i < len(p2) else 0
            res[i] = v1 + v2
        q_text = f"({s1})+({s2})"
    elif op == '-':
        max_len = max(len(p1), len(p2))
        res = [0] * max_len
        for i in range(max_len):
            v1 = p1[i] if i < len(p1) else 0
            v2 = p2[i] if i < len(p2) else 0
            res[i] = v1 - v2
        q_text = f"({s1})-({s2})"
    else:
        res = [0] * (len(p1) + len(p2) - 1)
        for i in range(len(p1)):
            for j in range(len(p2)):
                res[i+j] += p1[i] * p2[j]
        q_text = f"({s1})({s2})"
    return {
        'question_text': f"${q_text}$",
        'answer': '',
        'correct_answer': poly_to_str(res),
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}