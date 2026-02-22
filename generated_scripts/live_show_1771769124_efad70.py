import random

def generate(level=1, **kwargs):
    def to_str(c, space=False):
        res = ""
        d = list(range(len(c)-1, -1, -1))
        for i in range(len(c)):
            v = c[i]
            if v == 0: continue
            sign = " + " if v > 0 else " - "
            if not space: sign = "+" if v > 0 else "-"
            if not res: sign = "-" if v < 0 else ""
            av = abs(v)
            co = str(av) if (av != 1 or d[i] == 0) else ""
            va = "x" if d[i] == 1 else (f"x^{d[i]}" if d[i] > 1 else "")
            res += sign + co + va
        return res if res else "0"
    t = random.choice(['add', 'sub', 'mul', 'div'])
    if t in ['add', 'sub']:
        c1 = [random.randint(-9, 9) for _ in range(3)]
        c2 = [random.randint(-9, 9) for _ in range(3)]
        if all(x == 0 for x in c1): c1[0] = 1
        if all(x == 0 for x in c2): c2[0] = 1
        if t == 'add':
            ac = [c1[i] + c2[i] for i in range(3)]
            op = "+"
        else:
            ac = [c1[i] - c2[i] for i in range(3)]
            op = "-"
        q = f"Calculate $({to_str(c1, True)}) {op} ({to_str(c2, True)})$. "
        ans = to_str(ac, False)
    elif t == 'mul':
        c1 = [random.randint(-5, 5) for _ in range(2)]
        c2 = [random.randint(-5, 5) for _ in range(2)]
        if c1[0] == 0: c1[0] = 1
        if c2[0] == 0: c2[0] = 1
        ac = [c1[0]*c2[0], c1[0]*c2[1] + c1[1]*c2[0], c1[1]*c2[1]]
        q = f"Calculate $({to_str(c1, True)})({to_str(c2, True)})$. "
        ans = to_str(ac, False)
    else:
        c_ans = [random.randint(-5, 5) for _ in range(2)]
        c_div = [random.randint(-5, 5) for _ in range(2)]
        if c_ans[0] == 0: c_ans[0] = 1
        if c_div[0] == 0: c_div[0] = 1
        c_poly = [c_ans[0]*c_div[0], c_ans[0]*c_div[1] + c_ans[1]*c_div[0], c_ans[1]*c_div[1]]
        q = f"Calculate $({to_str(c_poly, True)}) \\div ({to_str(c_div, True)})$. "
        ans = to_str(c_ans, False)
    return {
        'question_text': q.strip(),
        'answer': '',
        'correct_answer': ans,
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}