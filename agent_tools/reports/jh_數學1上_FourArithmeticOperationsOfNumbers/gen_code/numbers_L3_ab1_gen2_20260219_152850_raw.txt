import random
from fractions import Fraction

def generate(level=1, **kwargs):
    def fmt_f(f, p=False):
        s = str(f)
        return f"({s})" if (p and f < 0) else s

    a = random.randint(-10, 10)
    b = random.randint(-10, 10)
    c = random.randint(-5, 5)
    d = random.randint(2, 6)
    e = random.choice([i for i in range(-5, 6) if i != 0])
    f = random.randint(2, 6)
    g = random.randint(-8, 8)
    h = random.randint(-5, 5)
    i = random.randint(2, 6)
    j = random.randint(-10, 10)

    frac1 = Fraction(c, d)
    frac2 = Fraction(e, f)
    frac3 = Fraction(h, i)

    term1_val = (Fraction(a) + Fraction(b)) * frac1 / frac2
    term2_val = abs(Fraction(g) * frac3 + Fraction(j))
    
    op = random.choice(['+', '-'])
    if op == '+':
        ans_val = term1_val + term2_val
    else:
        ans_val = term1_val - term2_val

    part1 = f"[({a}{'+' if b>=0 else ''}{b})×{fmt_f(frac1, True)}]÷{fmt_f(frac2, True)}"
    part2 = f"|{g}×{fmt_f(frac3, True)}{'+' if j>=0 else ''}{j}|"
    
    q_text = f"計算 {part1} {op} {part2} 的值。"
    
    return {
        'question_text': q_text,
        'answer': '',
        'correct_answer': str(ans_val),
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        ua = user_answer.strip().replace(' ', '')
        ca = correct_answer.strip().replace(' ', '')
        is_correct = Fraction(ua) == Fraction(ca)
    except:
        is_correct = user_answer.strip() == correct_answer.strip()
    
    return {
        'correct': is_correct,
        'result': '正確' if is_correct else '錯誤'
    }