import random

def poly_to_latex(coeffs, shuffle=False):
    terms = []
    for i, c in enumerate(coeffs):
        if c == 0:
            continue
        term = ""
        if i == 0:
            term = str(abs(c))
        elif i == 1:
            term = "x" if abs(c) == 1 else f"{abs(c)}x"
        else:
            term = f"x^{{{i}}}" if abs(c) == 1 else f"{abs(c)}x^{{{i}}}"
        terms.append({'deg': i, 'text': term, 'coeff': c})
    
    if not terms:
        return "0"
    
    if shuffle:
        random.shuffle(terms)
    else:
        terms.sort(key=lambda x: x['deg'], reverse=True)
    
    res = ""
    for i, item in enumerate(terms):
        c = item['coeff']
        t = item['text']
        if i == 0:
            res += ("-" if c < 0 else "") + t
        else:
            res += ("+" if c > 0 else "-") + t
    return res

def generate(level=1, **kwargs):
    if level == 1:
        op = random.choice(['+', '-'])
        p1 = [random.randint(-5, 5) for _ in range(random.randint(1, 3))]
        p2 = [random.randint(-5, 5) for _ in range(random.randint(1, 3))]
        while all(c == 0 for c in p1): p1 = [random.randint(-5, 5) for _ in range(2)]
        while all(c == 0 for c in p2): p2 = [random.randint(-5, 5) for _ in range(2)]
        
        size = max(len(p1), len(p2))
        res_coeffs = [0] * size
        for i in range(size):
            v1 = p1[i] if i < len(p1) else 0
            v2 = p2[i] if i < len(p2) else 0
            res_coeffs[i] = v1 + v2 if op == '+' else v1 - v2
        
        q_text = f"$({poly_to_latex(p1, True)}) {op} ({poly_to_latex(p2, True)})$"
        ans_text = poly_to_latex(res_coeffs)
        
    elif level == 2:
        p1 = [random.randint(-3, 3) for _ in range(random.randint(1, 2))]
        p2 = [random.randint(-3, 3) for _ in range(random.randint(1, 2))]
        while all(c == 0 for c in p1): p1 = [random.randint(-3, 3) for _ in range(2)]
        while all(c == 0 for c in p2): p2 = [random.randint(-3, 3) for _ in range(2)]
        
        res_coeffs = [0] * (len(p1) + len(p2) - 1)
        for i, a in enumerate(p1):
            for j, b in enumerate(p2):
                res_coeffs[i+j] += a * b
        
        q_text = f"$({poly_to_latex(p1, True)})({poly_to_latex(p2, True)})$"
        ans_text = poly_to_latex(res_coeffs)
        
    else:
        divisor = [random.randint(-3, 3), random.choice([-1, 1])]
        quotient = [random.randint(-3, 3) for _ in range(random.randint(1, 2))]
        while all(c == 0 for c in quotient): quotient = [random.randint(-3, 3) for _ in range(2)]
        remainder = [random.randint(-5, 5)]
        
        dividend = [0] * (len(divisor) + len(quotient) - 1)
        for i, a in enumerate(divisor):
            for j, b in enumerate(quotient):
                dividend[i+j] += a * b
        for i, r in enumerate(remainder):
            dividend[i] += r
            
        q_text = f"$({poly_to_latex(dividend)}) \\div ({poly_to_latex(divisor)})$"
        ans_text = f"Q: {poly_to_latex(quotient)}, R: {poly_to_latex(remainder)}"

    return {
        'question_text': q_text,
        'answer': '',
        'correct_answer': ans_text,
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}