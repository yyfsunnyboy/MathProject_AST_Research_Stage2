import random
from fractions import Fraction

def generate(level=1, **kwargs):
    def pf(f):
        s = str(f)
        return f"({s})" if f < 0 else s

    a = random.randint(-10, 10)
    b = random.randint(-10, 10)
    while a + b == 0:
        b = random.randint(-10, 10)
    
    f1_n = random.randint(1, 9)
    f1_d = random.randint(2, 9)
    f1 = Fraction(f1_n, f1_d)
    
    f2_n = random.choice([i for i in range(-9, 10) if i != 0])
    f2_d = random.randint(2, 9)
    f2 = Fraction(f2_n, f2_d)
    
    n3 = random.randint(2, 12)
    f3_n = random.choice([-1, 1]) * random.randint(1, 5)
    f3_d = random.randint(2, 6)
    f3 = Fraction(f3_n, f3_d)
    
    n4 = random.randint(-10, 10)
    
    term1 = f"[({a}{'+' if b>=0 else ''}{b})×{f1}]÷{pf(f2)}"
    term2 = f"|{n3}×{pf(f3)}{'+' if n4>=0 else ''}{n4}|"
    
    q_text = f"計算 {term1} + {term2} 的值。"
    ans_val = (a + b) * f1 / f2 + abs(n3 * f3 + n4)
    
    return {
        'question_text': q_text,
        'answer': '',
        'correct_answer': str(ans_val),
        'mode': 1
    }

def check(user_answer, correct_answer):
    is_correct = str(user_answer).strip() == str(correct_answer).strip()
    return {
        'correct': is_correct,
        'result': '正確' if is_correct else '錯誤'
    }