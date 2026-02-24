import random

def simplify_radical(n):
    if n == 0: return 0, 1
    a, d, temp = 1, 2, abs(n)
    while d * d <= temp:
        if temp % (d * d) == 0:
            a *= d
            temp //= (d * d)
        else:
            d += 1
    return a if n > 0 else -a, temp

def format_radical(a, b):
    if a == 0: return "0"
    if b == 1: return str(a)
    if a == 1: return f"\\sqrt{{{b}}}"
    if a == -1: return f"-\\sqrt{{{b}}}"
    return f"{a}\\sqrt{{{b}}}"

def generate(level=1, **kwargs):
    if level == 1:
        base = random.choice([2, 3, 5, 7])
        c1 = random.randint(1, 10)
        c2 = random.randint(1, 10)
        op = random.choice(['+', '-'])
        n1, n2 = base * (c1**2), base * (c2**2)
        question = f"\\sqrt{{{n1}}} {op} \\sqrt{{{n2}}}"
        ans_c = c1 + c2 if op == '+' else c1 - c2
        answer = format_radical(ans_c, base)
    else:
        n1 = random.randint(2, 5)
        n2 = random.randint(2, 5)
        n3 = random.randint(6, 10)
        question = f"\\sqrt{{{n1}}} (\\sqrt{{{n2}}} + \\sqrt{{{n3}}})"
        a1, b1 = simplify_radical(n1 * n2)
        a2, b2 = simplify_radical(n1 * n3)
        term1 = format_radical(a1, b1)
        term2 = format_radical(a2, b2)
        answer = f"{term1} + {term2}"
    return {
        'question_text': f"Simplify ${question}$",
        'answer': '',
        'correct_answer': answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': 'Correct' if correct else 'Incorrect'}