import random

def get_sq_free(n):
    a, b, d = 1, n, 2
    while d * d <= b:
        while b % (d * d) == 0:
            a *= d
            b //= (d * d)
        d += 1
    return a, b

def generate(level=1, **kwargs):
    res = {}
    def add_to_res(c, r):
        if r == 0 or c == 0: return
        a, b = get_sq_free(r)
        res[b] = res.get(b, 0) + c * a

    rads = [2, 3, 5, 6, 7, 8, 10, 12, 18, 20, 24, 27, 32, 48, 50]
    if level == 1:
        n1, n2, n3 = random.sample(rads, 3)
        k = random.randint(1, 3)
        q = f"\\sqrt{{{n1}}} + \\sqrt{{{n2}}} - {k if k > 1 else ''}\\sqrt{{{n3}}}"
        add_to_res(1, n1)
        add_to_res(1, n2)
        add_to_res(-k, n3)
    else:
        n1, n2, n3 = random.sample(rads[:10], 3)
        n4, n5, n6 = random.sample([2, 3, 5, 6, 7], 3)
        k1, k2 = random.randint(1, 3), random.randint(1, 3)
        q = f"(\\sqrt{{{n1}}} + \\sqrt{{{n2}}} - {k1 if k1 > 1 else ''}\\sqrt{{{n3}}}) + (\\sqrt{{{n4}}} + \\sqrt{{{n5}}})(\\sqrt{{{n6}}} - {k2})"
        add_to_res(1, n1)
        add_to_res(1, n2)
        add_to_res(-k1, n3)
        add_to_res(1, n4 * n6)
        add_to_res(-k2, n4)
        add_to_res(1, n5 * n6)
        add_to_res(-k2, n5)

    items = sorted(res.keys())
    p = []
    for r in items:
        c = res[r]
        if c == 0: continue
        if r == 1:
            s = str(c)
        else:
            pre = "" if c == 1 else "-" if c == -1 else str(c)
            s = f"{pre}\\sqrt{{{r}}}"
        if not p:
            p.append(s)
        else:
            if c > 0:
                p.append(f" + {s}")
            else:
                p.append(f" - {s[1:]}")
    ans = "".join(p) if p else "0"
    
    return {
        'question_text': f"Simplify ${q}$",
        'answer': '',
        'correct_answer': ans,
        'mode': 1
    }

def check(user_answer, correct_answer):
    c = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': c, 'result': 'Correct' if c else 'Incorrect'}