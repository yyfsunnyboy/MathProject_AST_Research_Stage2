import random
from fractions import Fraction

def generate(level=1, **kwargs):
    def f_s(f, p=False):
        s = str(f.numerator) if f.denominator == 1 else f"{f.numerator}/{f.denominator}"
        return f"({s})" if p and f < 0 else s
    
    n1 = random.randint(-9, 9)
    n2 = random.randint(-9, 9)
    while n1 + n2 == 0:
        n2 = random.randint(-9, 9)
    
    f1 = Fraction(random.randint(1, 7), random.randint(2, 7))
    
    f2_num = random.choice([i for i in range(-7, 8) if i != 0])
    f2 = Fraction(f2_num, random.randint(2, 7))
    
    n3 = random.randint(2, 10)
    f3_num = random.choice([-1, 1]) * random.randint(1, 5)
    f3 = Fraction(f3_num, random.randint(2, 7))
    
    n4 = random.randint(1, 10)
    
    res = ((n1 + n2) * f1) / f2 + abs(n3 * f3 - n4)
    
    s1 = str(n1)
    s2 = f"+{n2}" if n2 >= 0 else str(n2)
    q_text = f"[({s1}{s2})×{f_s(f1)}]÷{f_s(f2, True)} + |{n3}×{f_s(f3, True)}-{n4}|"
    
    ans_str = str(res.numerator) if res.denominator == 1 else f"{res.numerator}/{res.denominator}"
    
    return {
        'question_text': f"計算 {q_text} 的值。",
        'answer': '',
        'correct_answer': ans_str,
        'mode': 1
    }

def check(user_answer, correct_answer):
    u = str(user_answer).strip().replace(" ", "")
    c = str(correct_answer).strip().replace(" ", "")
    is_correct = (u == c)
    return {
        'correct': is_correct,
        'result': '正確' if is_correct else '錯誤'
    }