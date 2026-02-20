import random

def generate(level=1, **kwargs):
    def simplify(c, r):
        if r == 0: return 0, 1
        a, b, d = 1, r, 2
        while d * d <= b:
            if b % (d * d) == 0:
                a *= d
                b //= (d * d)
            else:
                d += 1
        return c * a, b

    def format_latex(terms):
        keys = sorted([k for k in terms if terms[k] != 0])
        if not keys: return "0"
        res = ""
        for k in keys:
            c = terms[k]
            if c > 0:
                if res: res += " + "
            else:
                if res: res += " - "
                else: res += "-"
            abs_c = abs(c)
            if abs_c != 1 or k == 1:
                res += str(abs_c)
            if k != 1:
                res += "\\sqrt{" + str(k) + "}"
        return res

    res_terms = {}
    if level == 1:
        q_parts = []
        for i in range(3):
            c = random.randint(1, 4) * random.choice([-1, 1])
            b = random.choice([2, 3, 5, 6])
            m = random.choice([1, 4, 9])
            r = b * m
            co, ra = simplify(c, r)
            res_terms[ra] = res_terms.get(ra, 0) + co
            part = ""
            if not q_parts:
                if c < 0: part = "-"
            else:
                part = " + " if c > 0 else " - "
            abs_c = abs(c)
            if abs_c != 1: part += str(abs_c)
            part += "\\sqrt{" + str(r) + "}"
            q_parts.append(part)
        q = "".join(q_parts)
    elif level == 2:
        c1, c2, c3, c4 = [random.choice([2, 3, 5]) for _ in range(4)]
        for r in [c1*c3, c1*c4, c2*c3, c2*c4]:
            co, ra = simplify(1, r)
            res_terms[ra] = res_terms.get(ra, 0) + co
        q = f"(\\sqrt{{{c1}}} + \\sqrt{{{c2}}})(\\sqrt{{{c3}}} + \\sqrt{{{c4}}})"
    else:
        c1, c2, c3 = [random.choice([2, 3, 5]) for _ in range(3)]
        for r in [c1*c3, c2*c3]:
            co, ra = simplify(1, r)
            res_terms[ra] = res_terms.get(ra, 0) + co
        p1_text = ""
        for i in range(2):
            c = random.randint(1, 2) * random.choice([-1, 1])
            b = random.choice([2, 3])
            m = random.choice([1, 4])
            r = b * m
            co, ra = simplify(c, r)
            res_terms[ra] = res_terms.get(ra, 0) + co
            t = ""
            if not p1_text:
                if c < 0: t = "-"
            else:
                t = " + " if c > 0 else " - "
            abs_c = abs(c)
            if abs_c != 1: t += str(abs_c)
            t += "\\sqrt{" + str(r) + "}"
            p1_text += t
        q = f"({p1_text}) + (\\sqrt{{{c1}}} + \\sqrt{{{c2}}})\\sqrt{{{c3}}}"

    return {
        'question_text': f'Simplify ${q}$',
        'answer': '',
        'correct_answer': format_latex(res_terms),
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}