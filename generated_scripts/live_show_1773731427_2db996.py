import random
import math

def simplify_sqrt(n):
    coeff = 1
    d = 2
    temp = n
    while d * d <= temp:
        while temp % (d * d) == 0:
            coeff *= d
            temp //= (d * d)
        d += 1
    return coeff, temp

def format_term(c, r):
    if c == 0:
        return "0"
    if r == 1:
        return str(c)
    if c == 1:
        return f"\\sqrt{{{r}}}"
    if c == -1:
        return f"-\\sqrt{{{r}}}"
    return f"{c}\\sqrt{{{r}}}"

def generate(level=1, **kwargs):
    problem_type = random.randint(1, 4)
    
    if problem_type == 1:
        # Addition and Subtraction
        r = random.choice([2, 3, 5, 6, 7, 10, 11])
        a = random.randint(1, 12)
        b = random.randint(1, 12)
        op = random.choice(['+', '-'])
        question_text = f"${a}\\sqrt{{{r}}} {op} {b}\\sqrt{{{r}}}$"
        ans_c = a + b if op == '+' else a - b
        correct_answer = format_term(ans_c, r)
        
    elif problem_type == 2:
        # Simple Multiplication
        a = random.randint(2, 15)
        b = random.randint(2, 15)
        question_text = f"$\\sqrt{{{a}}} \\times \\sqrt{{{b}}}$"
        c, r = simplify_sqrt(a * b)
        correct_answer = format_term(c, r)
        
    elif problem_type == 3:
        # Simple Division / Rationalization
        a = random.randint(2, 10)
        b = random.randint(2, 10)
        question_text = f"$\\frac{{\\sqrt{{{a}}}}}{{\\sqrt{{{b}}}}}$"
        # sqrt(a/b) = sqrt(ab)/b
        num = a
        den = b
        common_factor = math.gcd(num, den)
        n = num // common_factor
        d = den // common_factor
        val = n * d
        co, rad = simplify_sqrt(val)
        g = math.gcd(co, d)
        final_co = co // g
        final_den = d // g
        top = format_term(final_co, rad)
        if final_den == 1:
            correct_answer = top
        else:
            correct_answer = f"\\frac{{{top}}}{{{final_den}}}"
            
    else:
        # Complex Division (Reference Example Style)
        a = random.randint(2, 6)
        b = random.randint(2, 8)
        c = random.randint(2, 8)
        question_text = f"$\\frac{{1}}{{\\sqrt{{{a}}}}} \\div \\frac{{\\sqrt{{{b}}}}}{{\\sqrt{{{c}}}}}$"
        # 1/sqrt(a) * sqrt(c)/sqrt(b) = sqrt(c)/sqrt(ab)
        num = c
        den = a * b
        common_factor = math.gcd(num, den)
        n = num // common_factor
        d = den // common_factor
        val = n * d
        co, rad = simplify_sqrt(val)
        g = math.gcd(co, d)
        final_co = co // g
        final_den = d // g
        top = format_term(final_co, rad)
        if final_den == 1:
            correct_answer = top
        else:
            correct_answer = f"\\frac{{{top}}}{{{final_den}}}"

    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}