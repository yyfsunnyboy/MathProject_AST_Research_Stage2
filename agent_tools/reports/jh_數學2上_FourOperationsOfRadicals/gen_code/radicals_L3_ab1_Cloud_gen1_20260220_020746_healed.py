import random

def _get_radical_parts(n):
    coeff = 1
    d = 2
    temp = n
    while d * d <= temp:
        while temp % (d * d) == 0:
            coeff *= d
            temp //= (d * d)
        d += 1
    return coeff, temp

def _format_term(c, r):
    if c == 0:
        return ""
    if r == 1:
        return str(c)
    if c == 1:
        return f"\\sqrt{{{r}}}"
    if c == -1:
        return f"-\\sqrt{{{r}}}"
    return f"{c}\\sqrt{{{r}}}"

def _format_expression(terms):
    sorted_radicals = sorted(terms.keys(), reverse=True)
    result = ""
    for r in sorted_radicals:
        c = terms[r]
        if c == 0:
            continue
        term_str = _format_term(c, r)
        if not result:
            result = term_str
        else:
            if c > 0:
                result += " + " + term_str
            else:
                result += " - " + _format_term(abs(c), r)
    return result if result else "0"

def generate(level=1, **kwargs):
    problem_type = random.randint(1, 3)
    terms = {}
    
    if problem_type == 1:
        base_rad = random.choice([2, 3, 5, 6, 7, 10])
        c1 = random.randint(1, 6)
        c2 = random.randint(1, 6)
        c3 = random.randint(1, 6)
        n1, n2, n3 = (c1**2) * base_rad, (c2**2) * base_rad, (c3**2) * base_rad
        op = random.choice(['+', '-'])
        if op == '+':
            question = f"\\sqrt{{{n1}}} + \\sqrt{{{n2}}} - \\sqrt{{{n3}}}"
            ans_coeff = c1 + c2 - c3
        else:
            question = f"\\sqrt{{{n1}}} - \\sqrt{{{n2}}} + \\sqrt{{{n3}}}"
            ans_coeff = c1 - c2 + c3
        terms[base_rad] = ans_coeff
        
    elif problem_type == 2:
        a = random.randint(2, 15)
        b = random.randint(2, 15)
        question = f"\\sqrt{{{a}}} \\times \\sqrt{{{b}}}"
        c, r = _get_radical_parts(a * b)
        terms[r] = c
        
    else:
        a = random.randint(2, 5)
        b = random.randint(2, 8)
        c = random.randint(2, 8)
        question = f"\\sqrt{{{a}}}(\\sqrt{{{b}}} + \\sqrt{{{c}}})"
        c1, r1 = _get_radical_parts(a * b)
        c2, r2 = _get_radical_parts(a * c)
        terms[r1] = terms.get(r1, 0) + c1
        terms[r2] = terms.get(r2, 0) + c2

    return {
        'question_text': f"${question}$",
        'answer': '',
        'correct_answer': _format_expression(terms),
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}