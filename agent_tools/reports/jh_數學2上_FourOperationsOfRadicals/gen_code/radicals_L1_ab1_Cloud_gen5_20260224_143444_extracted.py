import random

def simplify_radical(n):
    if n <= 0: return 0, 1
    coeff = 1
    d = 2
    temp = n
    while d * d <= temp:
        while temp % (d * d) == 0:
            coeff *= d
            temp //= (d * d)
        d += 1
    return coeff, temp

def format_term(coeff, inside):
    if coeff == 0: return ""
    if inside == 1: return str(coeff)
    s_coeff = ""
    if coeff == 1: s_coeff = ""
    elif coeff == -1: s_coeff = "-"
    else: s_coeff = str(coeff)
    return s_coeff + "\\sqrt{" + str(inside) + "}"

def format_expression(terms_dict):
    sorted_keys = sorted(terms_dict.keys())
    parts = []
    for k in sorted_keys:
        c = terms_dict[k]
        if c == 0: continue
        term = format_term(c, k)
        if not parts:
            parts.append(term)
        else:
            if c > 0:
                parts.append(" + " + term)
            else:
                parts.append(" - " + term[1:] if term.startswith("-") else " + " + term)
    if not parts: return "0"
    return "".join(parts).strip()

def generate(level=1, **kwargs):
    base = random.choice([2, 3, 5, 6, 7, 10])
    def get_rand_term():
        co = random.randint(1, 3)
        sq = random.randint(1, 3)**2
        return co, sq * base
    t1_c, t1_n = get_rand_term()
    t2_c, t2_n = get_rand_term()
    t3_c, t3_n = get_rand_term()
    t3_c = -t3_c
    primes = [2, 3, 5, 7, 11]
    random.shuffle(primes)
    a_in, b_in, c_in = primes[0], primes[1], primes[2]
    k_val = random.randint(-3, 3)
    if k_val == 0: k_val = 1
    final_terms = {}
    def add_to_final(c, i):
        co, ins = simplify_radical(i)
        real_c = c * co
        if real_c == 0: return
        final_terms[ins] = final_terms.get(ins, 0) + real_c
    s1_co, _ = simplify_radical(t1_n)
    add_to_final(t1_c * s1_co, base)
    s2_co, _ = simplify_radical(t2_n)
    add_to_final(t2_c * s2_co, base)
    s3_co, _ = simplify_radical(t3_n)
    add_to_final(t3_c * s3_co, base)
    add_to_final(1, a_in * c_in)
    add_to_final(k_val, a_in)
    add_to_final(1, b_in * c_in)
    add_to_final(k_val, b_in)
    ans_str = format_expression(final_terms)
    def fmt_q_term(c, n):
        if c == 1: return f"\\sqrt{{{n}}}"
        if c == -1: return f"-\\sqrt{{{n}}}"
        return f"{c}\\sqrt{{{n}}}"
    q1 = fmt_q_term(t1_c, t1_n)
    q2 = fmt_q_term(t2_c, t2_n)
    q3 = fmt_q_term(t3_c, t3_n)
    q_part1 = q1
    for q in [q2, q3]:
        if q.startswith("-"): q_part1 += " - " + q[1:]
        else: q_part1 += " + " + q
    q_part2 = f"(\\sqrt{{{a_in}}} + \\sqrt{{{b_in}}})(\\sqrt{{{c_in}}} {'+' if k_val > 0 else '-'} {abs(k_val)})"
    return {
        'question_text': f"Simplify $({q_part1}) + {q_part2}$",
        'answer': '',
        'correct_answer': ans_str,
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}