import random

def poly_to_str(p):
    terms = []
    deg = len(p) - 1
    for i in range(deg, -1, -1):
        c = p[i]
        if c == 0:
            continue
        s = ""
        if c > 0:
            if terms:
                s += "+"
        else:
            s += "-"
        abs_c = abs(c)
        if abs_c != 1 or i == 0:
            s += str(abs_c)
        if i > 0:
            s += "x"
            if i > 1:
                s += "^" + str(i)
        terms.append(s)
    return "".join(terms) if terms else "0"

def get_rand_poly(deg):
    p = [random.randint(-10, 10) for _ in range(deg)]
    p.append(random.choice([i for i in range(-10, 11) if i != 0]))
    return p

def add_poly(p1, p2):
    size = max(len(p1), len(p2))
    res = [0] * size
    for i in range(size):
        v1 = p1[i] if i < len(p1) else 0
        v2 = p2[i] if i < len(p2) else 0
        res[i] = v1 + v2
    return res

def sub_poly(p1, p2):
    size = max(len(p1), len(p2))
    res = [0] * size
    for i in range(size):
        v1 = p1[i] if i < len(p1) else 0
        v2 = p2[i] if i < len(p2) else 0
        res[i] = v1 - v2
    return res

def mul_poly(p1, p2):
    res = [0] * (len(p1) + len(p2) - 1)
    for i in range(len(p1)):
        for j in range(len(p2)):
            res[i+j] += p1[i] * p2[j]
    return res

def generate(level=1, **kwargs):
    if level == 2:
        p1 = get_rand_poly(1)
        p2 = get_rand_poly(1)
        res = mul_poly(p1, p2)
        q_text = f"$({poly_to_str(p1)})({poly_to_str(p2)})$"
    elif level == 3:
        q = get_rand_poly(1)
        b = get_rand_poly(1)
        a = mul_poly(q, b)
        res = q
        q_text = f"$({poly_to_str(a)}) \\div ({poly_to_str(b)})$"
    else:
        p1 = get_rand_poly(random.randint(1, 2))
        p2 = get_rand_poly(random.randint(1, 2))
        op = random.choice(['+', '-'])
        if op == '+':
            res = add_poly(p1, p2)
            q_text = f"$({poly_to_str(p1)}) + ({poly_to_str(p2)})$"
        else:
            res = sub_poly(p1, p2)
            q_text = f"$({poly_to_str(p1)}) - ({poly_to_str(p2)})$"
    
    return {
        'question_text': q_text,
        'answer': '',
        'correct_answer': poly_to_str(res),
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}