import random

def simplify(c, r):
    i = 2
    while i * i <= r:
        while r % (i * i) == 0:
            c *= i
            r //= (i * i)
        i += 1
    return c, r

def format_latex(d):
    res = ""
    for r in sorted(d.keys()):
        c = d[r]
        if c == 0: continue
        if c > 0:
            res += " + "
        else:
            res += " - "
        abs_c = abs(c)
        if r == 1:
            res += str(abs_c)
        else:
            if abs_c != 1:
                res += str(abs_c)
            res += f"\\sqrt{{{r}}}"
    if not res: return "0"
    res = res.strip()
    if res.startswith("+ "):
        res = res[2:]
    elif res.startswith("- "):
        res = "-" + res[2:]
    return res

def get_val():
    b = random.choice([1, 2, 3, 5, 6, 7])
    s = random.randint(1, 4)
    c = random.randint(1, 2)
    if b == 1:
        s = 1
    return c, s*s*b, c*s, b

def get_q_term(c, n, first=False):
    if c < 0:
        s = "-" if first else " - "
    else:
        s = "" if first else " + "
    abs_c = abs(c)
    if n == 1:
        return f"{s}{abs_c}"
    c_str = str(abs_c) if abs_c != 1 else ""
    return f"{s}{c_str}\\sqrt{{{n}}}"

def generate(level=1, **kwargs):
    if level == 1:
        d = {}
        q = ""
        for i in range(3):
            c, n, sc, b = get_val()
            sig = 1 if i == 0 else random.choice([1, -1])
            d[b] = d.get(b, 0) + sig * sc
            q += get_q_term(sig * c, n, i == 0)
        return {'question_text': f"${q}$", 'answer': '', 'correct_answer': format_latex(d), 'mode': 1}
    elif level == 2:
        c1, n1, sc1, b1 = get_val()
        c2, n2, sc2, b2 = get_val()
        c3, n3, sc3, b3 = get_val()
        c4, n4, sc4, b4 = get_val()
        sig2 = random.choice([1, -1])
        sig4 = random.choice([1, -1])
        q = f"({get_q_term(c1, n1, True)}{get_q_term(sig2*c2, n2)})({get_q_term(c3, n3, True)}{get_q_term(sig4*c4, n4)})"
        d = {}
        for r_a, c_a in [(b1, sc1), (b2, sig2*sc2)]:
            for r_b, c_b in [(b3, sc3), (b4, sig4*sc4)]:
                c_new, r_new = simplify(c_a * c_b, r_a * r_b)
                d[r_new] = d.get(r_new, 0) + c_new
        return {'question_text': f"${q}$", 'answer': '', 'correct_answer': format_latex(d), 'mode': 1}
    else:
        c1, n1, sc1, b1 = get_val()
        c2, n2, sc2, b2 = get_val()
        sig2 = random.choice([1, -1])
        q1 = f"({get_q_term(c1, n1, True)}{get_q_term(sig2*c2, n2)})"
        d = {b1: d.get(b1, 0) + sc1, b2: d.get(b2, 0) + sig2*sc2} if 'd' in locals() else {b1: sc1, b2: sig2*sc2}
        c3, n3, sc3, b3 = get_val()
        c4, n4, sc4, b4 = get_val()
        c5, n5, sc5, b5 = get_val()
        c6, n6, sc6, b6 = get_val()
        sig4 = random.choice([1, -1])
        sig6 = random.choice([1, -1])
        q2 = f"({get_q_term(c3, n3, True)}{get_q_term(sig4*c4, n4)})({get_q_term(c5, n5, True)}{get_q_term(sig6*c6, n6)})"
        for r_a, c_a in [(b3, sc3), (b4, sig4*sc4)]:
            for r_b, c_b in [(b5, sc5), (b6, sig6*sc6)]:
                c_new, r_new = simplify(c_a * c_b, r_a * r_b)
                d[r_new] = d.get(r_new, 0) + c_new
        return {'question_text': f"${q1} + {q2}$", 'answer': '', 'correct_answer': format_latex(d), 'mode': 1}

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}