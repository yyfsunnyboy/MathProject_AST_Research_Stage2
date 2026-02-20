import random

def _simplify(c, n):
    coeff, base, d = c, n, 2
    while d * d <= base:
        while base % (d * d) == 0:
            coeff *= d
            base //= (d * d)
        d += 1
    return coeff, base

def _to_latex(terms):
    sorted_bases = sorted(terms.keys())
    res = ""
    for b in sorted_bases:
        c = terms[b]
        if c == 0: continue
        if c > 0 and res: res += "+"
        if b == 1: res += str(c)
        elif c == 1: res += "\\sqrt{" + str(b) + "}"
        elif c == -1: res += "-\\sqrt{" + str(b) + "}"
        else: res += str(c) + "\\sqrt{" + str(b) + "}"
    return res if res else "0"

def generate(level=1, **kwargs):
    final_terms = {}
    def add_to_final(c, b):
        co, ba = _simplify(c, b)
        final_terms[ba] = final_terms.get(ba, 0) + co

    if level == 1:
        q_parts = []
        for i in range(3):
            c = random.randint(1, 4)
            base = random.choice([2, 3, 5])
            val = base * (random.choice([1, 4, 9]))
            sign = 1 if i == 0 else random.choice([1, -1])
            add_to_final(sign * c, val)
            t_str = ""
            if sign == -1: t_str += "-"
            elif i > 0: t_str += "+"
            if c == 1: t_str += f"\\sqrt{{{val}}}"
            else: t_str += f"{c}\\sqrt{{{val}}}"
            q_parts.append(t_str)
        question = "".join(q_parts)
    else:
        a_v = random.choice([2, 3, 5])
        b_v = random.choice([2, 3, 5])
        c_v = random.choice([2, 3, 5])
        d_v = random.randint(1, 3)
        add_to_final(1, a_v * c_v)
        add_to_final(d_v, a_v)
        add_to_final(1, b_v * c_v)
        add_to_final(d_v, b_v)
        question = f"(\\sqrt{{{a_v}}} + \\sqrt{{{b_v}}})(\\sqrt{{{c_v}}} + {d_v})"
        if level >= 3:
            e_c = random.randint(1, 2)
            e_b = random.choice([2, 3, 5])
            e_val = e_b * random.choice([1, 4])
            add_to_final(e_c, e_val)
            question = f"\\sqrt{{{e_val}}} + " + question

    return {
        'question_text': f"Simplify ${question}$",
        'answer': '',
        'correct_answer': _to_latex(final_terms),
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}