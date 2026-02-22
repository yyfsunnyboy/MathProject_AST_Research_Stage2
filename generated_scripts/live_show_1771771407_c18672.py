import random

def format_p(p_dict, shuffle=False):
    items = list(p_dict.items())
    items = [it for it in items if it[1] != 0]
    if not items:
        return "0"
    if shuffle:
        random.shuffle(items)
    else:
        items.sort(key=lambda x: x[0], reverse=True)
    res = ""
    for i, (p, c) in enumerate(items):
        sign = "+" if c > 0 else "-"
        abs_c = abs(c)
        term = ""
        if abs_c != 1 or p == 0:
            term += str(abs_c)
        if p > 0:
            term += "x"
            if p > 1:
                term += "^" + str(p)
        if i == 0:
            if sign == "-":
                res += "-" + term
            else:
                res += term
        else:
            res += sign + term
    return res

def gen_p(deg_min=0, deg_max=2):
    p = {}
    deg = random.randint(deg_min, deg_max)
    for i in range(deg + 1):
        p[i] = random.randint(-9, 9)
    if all(v == 0 for v in p.values()):
        p[random.randint(0, deg)] = random.randint(1, 9)
    return p

def add_p(p1, p2):
    res = p1.copy()
    for p, c in p2.items():
        res[p] = res.get(p, 0) + c
    return res

def sub_p(p1, p2):
    res = p1.copy()
    for p, c in p2.items():
        res[p] = res.get(p, 0) - c
    return res

def mul_p(p1, p2):
    res = {}
    for po1, co1 in p1.items():
        for po2, co2 in p2.items():
            p = po1 + po2
            res[p] = res.get(p, 0) + co1 * co2
    return res

def generate(level=1, **kwargs):
    t = random.randint(1, 4)
    if t == 1:
        p1, p2 = gen_p(0, level), gen_p(0, level)
        q = f"({format_p(p1, True)}) + ({format_p(p2, True)})"
        ans = add_p(p1, p2)
    elif t == 2:
        p1, p2 = gen_p(0, level), gen_p(0, level)
        q = f"({format_p(p1, True)}) - ({format_p(p2, True)})"
        ans = sub_p(p1, p2)
    elif t == 3:
        p1, p2, p3 = gen_p(0, level), gen_p(0, level), gen_p(0, level)
        q = f"({format_p(p1, True)}) - [({format_p(p2, True)}) - ({format_p(p3, True)})]"
        ans = add_p(sub_p(p1, p2), p3)
    else:
        p1, p2 = gen_p(0, 1), gen_p(0, level)
        q = f"({format_p(p1, True)})({format_p(p2, True)})"
        ans = mul_p(p1, p2)
    
    return {
        'question_text': f"Calculate ${q}$",
        'answer': '',
        'correct_answer': format_p(ans, False),
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}