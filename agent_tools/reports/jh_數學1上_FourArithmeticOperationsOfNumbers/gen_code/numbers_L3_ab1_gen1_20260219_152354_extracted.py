import random
from fractions import Fraction

def generate(level=1, **kwargs):
    def format_f(f, paren=False):
        s = str(f)
        if paren and f < 0:
            return f"({s})"
        return s

    def get_op_str(f):
        if f >= 0:
            return f"+{format_f(f)}"
        else:
            return f"-{format_f(abs(f))}"

    a = Fraction(random.randint(-10, 10), 1)
    b_val = random.randint(-10, 10)
    while b_val == 0:
        b_val = random.randint(-10, 10)
    b = Fraction(b_val, 1)
    
    c_num = random.randint(1, 5)
    c_den = random.randint(2, 6)
    c = Fraction(c_num, c_den)
    
    d_num = random.choice([i for i in range(-6, 7) if i != 0])
    d_den = random.randint(2, 5)
    d = Fraction(d_num, d_den)
    
    e = Fraction(random.randint(2, 12), 1)
    f_num = random.choice([i for i in range(-6, 7) if i != 0])
    f_den = random.randint(2, 6)
    f = Fraction(f_num, f_den)
    
    g_val = random.randint(-10, 10)
    while g_val == 0:
        g_val = random.randint(-10, 10)
    g = Fraction(g_val, 1)

    term1 = ((a + b) * c) / d
    term2 = abs(e * f + g)
    correct_val = term1 + term2

    expr_a_b = f"{format_f(a)}{get_op_str(b)}"
    part1 = f"[({expr_a_b})×{format_f(c)}]÷{format_f(d, True)}"
    part2 = f"|{format_f(e)}×{format_f(f, True)}{get_op_str(g)}|"
    
    question = f"計算 {part1} + {part2} 的值。"

    return {
        'question_text': question,
        'answer': '',
        'correct_answer': str(correct_val),
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