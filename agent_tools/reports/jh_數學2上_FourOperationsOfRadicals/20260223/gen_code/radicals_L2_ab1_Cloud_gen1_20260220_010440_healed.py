import random
import math

def get_radical(n):
    c, i = 1, n
    d = 2
    while d * d <= i:
        while i % (d * d) == 0:
            c *= d
            i //= (d * d)
        d += 1
    return c, i

def format_final(res_dict):
    sorted_bases = []
    if 1 in res_dict:
        sorted_bases.append(1)
    for b in sorted(res_dict.keys()):
        if b != 1:
            sorted_bases.append(b)
    parts = []
    for b in sorted_bases:
        c = res_dict[b]
        if c == 0:
            continue
        if b == 1:
            term = str(c)
        elif c == 1:
            term = f"\\sqrt{{{b}}}"
        elif c == -1:
            term = f"-\\sqrt{{{b}}}"
        else:
            term = f"{c}\\sqrt{{{b}}}"
        if c > 0 and parts:
            parts.append("+" + term)
        else:
            parts.append(term)
    res = "".join(parts)
    return res if res else "0"

def generate(level=1, **kwargs):
    res_dict = {}
    if level == 1:
        base = random.choice([2, 3, 5, 6, 7, 10])
        k = random.sample(range(1, 10), 3)
        n = [base * x * x for x in k]
        ops = [random.choice(['+', '-']), random.choice(['+', '-'])]
        q = f"\\sqrt{{{n[0]}}} {ops[0]} \\sqrt{{{n[1]}}} {ops[1]} \\sqrt{{{n[2]}}}"
        c1, i1 = get_radical(n[0])
        c2, i2 = get_radical(n[1])
        c3, i3 = get_radical(n[2])
        total = c1
        total = total + c2 if ops[0] == '+' else total - c2
        total = total + c3 if ops[1] == '+' else total - c3
        res_dict[base] = total
    elif level == 2:
        a = random.choice([2, 3, 5, 6])
        b, c = random.sample([2, 3, 5, 6, 7, 10], 2)
        s = random.choice(['+', '-'])
        q = f"\\sqrt{{{a}}}(\\sqrt{{{b}}} {s} \\sqrt{{{c}}})"
        for val, sign in [(a * b, 1), (a * c, 1 if s == '+' else -1)]:
            co, ins = get_radical(val)
            res_dict[ins] = res_dict.get(ins, 0) + (co * sign)
    else:
        a, b, c, d = random.sample([2, 3, 5, 6, 7, 10], 4)
        s1, s2 = random.choice(['+', '-']), random.choice(['+', '-'])
        q = f"(\\sqrt{{{a}}} {s1} \\sqrt{{{b}}})(\\sqrt{{{c}}} {s2} \\sqrt{{{d}}})"
        pairs = [
            (a * c, 1),
            (a * d, 1 if s2 == '+' else -1),
            (b * c, 1 if s1 == '+' else -1),
            (b * d, (1 if s1 == '+' else -1) * (1 if s2 == '+' else -1))
        ]
        for val, sign in pairs:
            co, ins = get_radical(val)
            res_dict[ins] = res_dict.get(ins, 0) + (co * sign)
    return {
        'question_text': f"Simplify ${q}$",
        'answer': '',
        'correct_answer': format_final(res_dict),
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}