import random
import math

def simplify_radical(n):
    coeff = 1
    d = 2
    temp = n
    while d * d <= temp:
        while temp % (d * d) == 0:
            coeff *= d
            temp //= (d * d)
        d += 1
    return coeff, temp

def format_latex(term_dict):
    sorted_rads = sorted(term_dict.keys())
    parts = []
    for r in sorted_rads:
        c = term_dict[r]
        if c == 0: continue
        parts.append((c, r))
    if not parts: return "0"
    res = ""
    for i, (c, r) in enumerate(parts):
        if i == 0:
            if c < 0: res += "-"
        else:
            res += " + " if c > 0 else " - "
        abs_c = abs(c)
        if r == 1:
            res += str(abs_c)
        else:
            if abs_c == 1:
                res += f"\\sqrt{{{r}}}"
            else:
                res += f"{abs_c}\\sqrt{{{r}}}"
    return res

def generate(level=1, **kwargs):
    bases = [2, 3, 5, 6, 7, 10]
    squares = [1, 4, 9, 16, 25]
    final_terms = {}
    def add_to_final(c, r):
        if c == 0: return
        co, ra = simplify_radical(r)
        total_c = c * co
        final_terms[ra] = final_terms.get(ra, 0) + total_c
    if level == 1:
        b = random.choice(bases)
        c1, c2, c3 = [random.randint(1, 3) for _ in range(3)]
        s1, s2, s3 = random.sample(squares, 3)
        v1, v2, v3 = s1*b, s2*b, s3*b
        t1 = f"\\sqrt{{{v1}}}"
        t2 = f"\\sqrt{{{v2}}}" if c2 == 1 else f"{c2}\\sqrt{{{v2}}}"
        t3 = f"\\sqrt{{{v3}}}" if c3 == 1 else f"{c3}\\sqrt{{{v3}}}"
        q_text = f"({t1} + {t2} - {t3})"
        add_to_final(1, v1)
        add_to_final(c2, v2)
        add_to_final(-c3, v3)
    elif level == 2:
        a, b, c, d = random.sample(range(2, 12), 4)
        q_text = f"(\\sqrt{{{a}}} + \\sqrt{{{b}}})(\\sqrt{{{c}}} - \\sqrt{{{d}}})"
        add_to_final(1, a*c)
        add_to_final(-1, a*d)
        add_to_final(1, b*c)
        add_to_final(-1, b*d)
    else:
        b1 = random.choice(bases)
        s1, s2 = random.sample(squares[1:], 2)
        v1, v2 = s1*b1, s2*b1
        d, e, f = random.sample(range(2, 10), 3)
        g = random.randint(1, 4)
        q_text = f"(\\sqrt{{{v1}}} - \\sqrt{{{v2}}}) + (\\sqrt{{{d}}} + \\sqrt{{{e}}})(\\sqrt{{{f}}} - {g})"
        add_to_final(1, v1)
        add_to_final(-1, v2)
        add_to_final(1, d*f)
        add_to_final(-g, d)
        add_to_final(1, e*f)
        add_to_final(-g, e)
    return {
        'question_text': f"${q_text}$",
        'answer': '',
        'correct_answer': format_latex(final_terms),
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}