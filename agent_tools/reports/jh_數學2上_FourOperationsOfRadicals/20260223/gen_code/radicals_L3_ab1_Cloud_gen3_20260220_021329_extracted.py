import random

def simplify(c, n):
    if n == 0:
        return 0, 0
    res_c, res_n = c, n
    d = 2
    while d * d <= res_n:
        if res_n % (d * d) == 0:
            res_c *= d
            res_n //= (d * d)
        else:
            d += 1
    return res_c, res_n

def to_latex(d):
    keys = sorted([k for k in d if d[k] != 0], reverse=True)
    if not keys:
        return "0"
    res = ""
    for i, k in enumerate(keys):
        v = d[k]
        if v > 0 and i > 0:
            res += "+"
        if v == -1 and k != 1:
            res += "-"
        elif v == 1 and k != 1:
            pass
        else:
            res += str(v)
        if k != 1:
            res += "\\sqrt{" + str(k) + "}"
    return res

def fmt_q(c, n):
    if n == 1:
        return str(c)
    if c == 1:
        return "\\sqrt{" + str(n) + "}"
    if c == -1:
        return "-\\sqrt{" + str(n) + "}"
    return str(c) + "\\sqrt{" + str(n) + "}"

def generate(level=1, **kwargs):
    nums = [2, 3, 5, 6, 7, 8, 10, 12, 18, 20, 24, 27, 32, 48, 50]
    res_dict = {}
    q_str = ""
    
    if level == 1:
        c1, n1 = random.randint(1, 3), random.choice(nums)
        c2, n2 = random.randint(-3, 3), random.choice(nums)
        c3, n3 = random.randint(-3, 3), random.choice(nums)
        if c2 == 0: c2 = 1
        if c3 == 0: c3 = 1
        for c, n in [(c1, n1), (c2, n2), (c3, n3)]:
            cs, ns = simplify(c, n)
            res_dict[ns] = res_dict.get(ns, 0) + cs
        q_str = f"{fmt_q(c1, n1)} {'+' if c2 > 0 else '-'} {fmt_q(abs(c2), n2)} {'+' if c3 > 0 else '-'} {fmt_q(abs(c3), n3)}"
    
    elif level == 2:
        n1 = random.choice([2, 3, 5, 6])
        n2 = random.choice(nums)
        n3 = random.choice(nums)
        for n in [n1 * n2, n1 * n3]:
            cs, ns = simplify(1, n)
            res_dict[ns] = res_dict.get(ns, 0) + cs
        q_str = f"\\sqrt{{{n1}}}(\\sqrt{{{n2}}} + \\sqrt{{{n3}}})"
        
    else:
        n1, n2 = random.choice(nums), random.choice(nums)
        n3, n4 = random.choice(nums), random.choice(nums)
        n5, n6 = random.choice([2, 3, 5]), random.choice([2, 3, 5])
        for c, n in [simplify(1, n1), simplify(1, n2)]:
            res_dict[n] = res_dict.get(n, 0) + c
        for na, nb in [(n3, n5), (n3, n6), (n4, n5), (n4, n6)]:
            cs, ns = simplify(1, na * nb)
            res_dict[ns] = res_dict.get(ns, 0) + cs
        q_str = f"(\\sqrt{{{n1}}} + \\sqrt{{{n2}}}) + (\\sqrt{{{n3}}} + \\sqrt{{{n4}}})(\\sqrt{{{n5}}} + \\sqrt{{{n6}}})"

    return {
        'question_text': f"Simplify ${q_str}$",
        'answer': '',
        'correct_answer': to_latex(res_dict),
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}