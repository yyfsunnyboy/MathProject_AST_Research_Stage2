import random

def generate(level=1, **kwargs):
    def p(n):
        return f"({n})" if n < 0 else str(n)
    
    l = max(1, level)
    case = random.randint(1, 5)
    
    if case == 1:
        a, b, c = random.randint(-10*l, 10*l), random.randint(-10*l, 10*l), random.randint(-10*l, 10*l)
        q = f"{p(a)}+{p(b)}×{p(c)}"
        ans = a + b * c
    elif case == 2:
        a, b, c = random.randint(-10*l, 10*l), random.randint(-10*l, 10*l), random.randint(-10*l, 10*l)
        q = f"{p(a)}-{p(b)}×{p(c)}"
        ans = a - b * c
    elif case == 3:
        divisor = random.randint(-5*l, 5*l)
        if divisor == 0: divisor = 1
        quotient = random.randint(-10*l, 10*l)
        dividend = divisor * quotient
        extra = random.randint(-10*l, 10*l)
        q = f"{p(dividend)}÷{p(divisor)}+{p(extra)}"
        ans = quotient + extra
    elif case == 4:
        a, b, c = random.randint(-10*l, 10*l), random.randint(-5*l, 5*l), random.randint(-5*l, 5*l)
        q = f"|{p(a)}-{p(b)}×{p(c)}|"
        ans = abs(a - b * c)
    else:
        a, b, c = random.randint(-10*l, 10*l), random.randint(-10*l, 10*l), random.randint(-10*l, 10*l)
        q = f"{p(a)}×({p(b)}-{p(c)})"
        ans = a * (b - c)
        
    return {
        'question_text': q,
        'answer': '',
        'correct_answer': str(ans),
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        ua = str(user_answer).strip()
        ca = str(correct_answer).strip()
        is_correct = int(ua) == int(ca)
    except:
        is_correct = False
    return {
        'correct': is_correct,
        'result': '正確' if is_correct else '錯誤'
    }