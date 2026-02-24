import random

def poly_to_str(coeffs):
    res = ""
    n = len(coeffs) - 1
    for i, c in enumerate(coeffs):
        p = n - i
        if c == 0:
            continue
        if c > 0:
            sign = "+" if res else ""
        else:
            sign = "-"
        val = abs(c)
        if p == 0:
            term = str(val)
        elif p == 1:
            term = "x" if val == 1 else f"{val}x"
        else:
            term = f"x^{p}" if val == 1 else f"{val}x^{p}"
        res += sign + term
    return res if res else "0"

def generate(level=1, **kwargs):
    if level == 1:
        p1 = [random.randint(-10, 10) for _ in range(3)]
        p2 = [random.randint(-10, 10) for _ in range(3)]
        while p1[0] == 0: p1[0] = random.randint(-10, 10)
        while p2[0] == 0: p2[0] = random.randint(-10, 10)
        op = random.choice(["+", "-"])
        s1 = poly_to_str(p1)
        s2 = poly_to_str(p2)
        if op == "+":
            ans = [p1[i] + p2[i] for i in range(3)]
            q = f"Calculate $({s1}) + ({s2})$"
        else:
            ans = [p1[i] - p2[i] for i in range(3)]
            q = f"Calculate $({s1}) - ({s2})$"
        ans_s = poly_to_str(ans)
    else:
        p1 = [random.randint(-5, 5) for _ in range(2)]
        p2 = [random.randint(-5, 5) for _ in range(3)]
        while p1[0] == 0: p1[0] = random.randint(-5, 5)
        while p2[0] == 0: p2[0] = random.randint(-5, 5)
        s1 = poly_to_str(p1)
        s2 = poly_to_str(p2)
        ans = [0] * 4
        for i in range(2):
            for j in range(3):
                ans[i+j] += p1[i] * p2[j]
        q = f"Expand and simplify $({s1})({s2})$"
        ans_s = poly_to_str(ans)
    return {'question_text': q, 'answer': '', 'correct_answer': ans_s, 'mode': 1}

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}