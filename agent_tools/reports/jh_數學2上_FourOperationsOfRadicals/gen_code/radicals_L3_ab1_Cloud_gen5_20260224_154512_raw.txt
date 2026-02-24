import random
import math

def simplify_radical(c, r):
    i = 2
    while i * i <= r:
        while r % (i * i) == 0:
            c *= i
            r //= (i * i)
        i += 1
    return c, r

def format_term(c, r, is_first=False):
    if c == 0:
        return ""
    res = ""
    if c > 0 and not is_first:
        res += "+"
    if r == 1:
        res += str(c)
    else:
        if c == 1:
            pass
        elif c == -1:
            res += "-"
        else:
            res += str(c)
        res += "\\sqrt{" + str(r) + "}"
    return res

def format_expr(res_dict):
    keys = sorted(res_dict.keys())
    res = ""
    first = True
    for r in keys:
        c = res_dict[r]
        if c == 0:
            continue
        term = format_term(c, r, first)
        res += term
        first = False
    return res if res else "0"

def generate(level=1, **kwargs):
    res_dict = {}
    primes = [2, 3, 5, 7, 11]
    if level == 1:
        q_str = ""
        for i in range(3):
            p = random.choice(primes)
            m = random.randint(1, 3)
            coeff = random.randint(1, 4)
            sign = random.choice([1, -1]) if i > 0 else 1
            val = (m**2) * p
            c_sim, r_sim = simplify_radical(sign * coeff, val)
            res_dict[r_sim] = res_dict.get(r_sim, 0) + c_sim
            q_str += format_term(sign * coeff, val, i == 0)
        question_text = f"Simplify ${q_str}$"
    elif level == 2:
        a_c, a_r = random.randint(1, 3), random.choice(primes)
        b_c, b_r = random.randint(1, 3), random.choice(primes)
        c_c, c_r = random.randint(1, 3), random.choice(primes)
        c1, r1 = simplify_radical(a_c * b_c, a_r * b_r)
        res_dict[r1] = res_dict.get(r1, 0) + c1
        c2, r2 = simplify_radical(a_c * c_c, a_r * c_r)
        res_dict[r2] = res_dict.get(r2, 0) + c2
        ta = format_term(a_c, a_r, True)
        tb = format_term(b_c, b_r, True)
        tc = format_term(c_c, c_r, False)
        question_text = f"Simplify ${ta}({tb}{tc})$"
    else:
        nums = random.sample([2, 3, 5, 6, 7, 8, 10], 4)
        a, b, c, d = nums
        for pair in [(a, c, 1), (a, d, -1), (b, c, 1), (b, d, -1)]:
            co, ra = simplify_radical(pair[2], pair[0] * pair[1])
            res_dict[ra] = res_dict.get(ra, 0) + co
        ta, tb = format_term(1, a, True), format_term(1, b, False)
        tc, td = format_term(1, c, True), format_term(-1, d, False)
        question_text = f"Simplify $({ta}{tb})({tc}{td})$"
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': format_expr(res_dict),
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}