import random

def simplify_sqrt(n):
    c, r = 1, n
    d = 2
    while d * d <= r:
        while r % (d * d) == 0:
            c *= d
            r //= (d * d)
        d += 1
    return c, r

def combine_terms(term_list):
    d = {}
    for c, r in term_list:
        if r == 0: continue
        d[r] = d.get(r, 0) + c
    sorted_roots = sorted(d.keys())
    parts = []
    for r in sorted_roots:
        coeff = d[r]
        if coeff == 0: continue
        if r == 1:
            t_str = str(abs(coeff))
        elif abs(coeff) == 1:
            t_str = f"\\sqrt{{{r}}}"
        else:
            t_str = f"{abs(coeff)}\\sqrt{{{r}}}"
        if not parts:
            parts.append("-" + t_str if coeff < 0 else t_str)
        else:
            parts.append(" - " + t_str if coeff < 0 else " + " + t_str)
    return "".join(parts) if parts else "0"

def generate(level=1, **kwargs):
    prob_type = random.randint(1, 2)
    if prob_type == 1:
        r = random.choice([2, 3, 5, 6, 7, 10])
        k1, k2, k3 = random.sample(range(1, 6), 3)
        v1, v2, v3 = (k1**2)*r, (k2**2)*r, (k3**2)*r
        ops = random.choice([("+", "+"), ("+", "-"), ("-", "+")])
        q = f"\\sqrt{{{v1}}} {ops[0]} \\sqrt{{{v2}}} {ops[1]} \\sqrt{{{v3}}}"
        res_c = k1
        res_c = res_c + k2 if ops[0] == "+" else res_c - k2
        res_c = res_c + k3 if ops[1] == "+" else res_c - k3
        ans = combine_terms([(res_c, r)])
    else:
        a = random.randint(2, 5)
        b = random.randint(2, 6)
        c = random.randint(2, 6)
        while b == c:
            c = random.randint(2, 6)
        q = f"\\sqrt{{{a}}}(\\sqrt{{{b}}} + \\sqrt{{{c}}})"
        v1, v2 = a * b, a * c
        s1c, s1r = simplify_sqrt(v1)
        s2c, s2r = simplify_sqrt(v2)
        ans = combine_terms([(s1c, s1r), (s2c, s2r)])
    return {
        'question_text': f"Simplify ${q}$",
        'answer': '',
        'correct_answer': ans,
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}