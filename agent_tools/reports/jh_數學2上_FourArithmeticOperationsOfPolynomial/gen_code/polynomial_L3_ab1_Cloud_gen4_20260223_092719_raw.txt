import random

def _format_poly(coeffs, is_latex=False):
    res = ""
    deg = len(coeffs) - 1
    for i, c in enumerate(coeffs):
        p = deg - i
        if c == 0: continue
        s = "+" if c > 0 and res else ""
        if c < 0: s = "-"
        ac = abs(c)
        v = str(ac) if (ac != 1 or p == 0) else ""
        t = ""
        if p == 1:
            t = "x"
        elif p > 1:
            t = "x^{" + str(p) + "}" if is_latex else "x^" + str(p)
        res += s + v + t
    return res if res else "0"

def generate(level=1, **kwargs):
    if level == 1:
        c1 = [random.randint(-9, 9) for _ in range(3)]
        c2 = [random.randint(-9, 9) for _ in range(3)]
        while all(x == 0 for x in c1): c1 = [random.randint(-9, 9) for _ in range(3)]
        while all(x == 0 for x in c2): c2 = [random.randint(-9, 9) for _ in range(3)]
        op = random.choice(['+', '-'])
        p1_tex = _format_poly(c1, True)
        p2_tex = _format_poly(c2, True)
        q = f"Calculate $({p1_tex}) {op} ({p2_tex})$"
        if op == '+':
            ans_c = [c1[i] + c2[i] for i in range(3)]
        else:
            ans_c = [c1[i] - c2[i] for i in range(3)]
        ans = _format_poly(ans_c, False)
    else:
        c1 = [random.randint(-5, 5) for _ in range(2)]
        c2 = [random.randint(-5, 5) for _ in range(3)]
        while c1[0] == 0: c1[0] = random.randint(-5, 5)
        while c2[0] == 0: c2[0] = random.randint(-5, 5)
        p1_tex = _format_poly(c1, True)
        p2_tex = _format_poly(c2, True)
        q = f"Expand and simplify $({p1_tex})({p2_tex})$"
        ans_c = [0] * 4
        ans_c[0] = c1[0] * c2[0]
        ans_c[1] = c1[0] * c2[1] + c1[1] * c2[0]
        ans_c[2] = c1[0] * c2[2] + c1[1] * c2[1]
        ans_c[3] = c1[1] * c2[2]
        ans = _format_poly(ans_c, False)
    return {
        'question_text': q,
        'answer': '',
        'correct_answer': ans,
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}