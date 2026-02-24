import random

def generate(level=1, **kwargs):
    a = random.randint(-30, 30)
    b = random.randint(-30, 30)
    sum_ab = a + b
    divisors = [i for i in range(-15, 16) if i != 0 and sum_ab % i == 0]
    c = random.choice(divisors)
    d = random.randint(-10, 10)
    e = random.randint(-10, 10)
    f = random.randint(-10, 10)
    g = random.randint(-20, 20)
    def p(n):
        return f"({n})" if n < 0 else str(n)
    part1_expr = f"[{p(a)}+{p(b)}]÷{p(c)}×{p(d)}"
    part1_val = (a + b) // c * d
    part2_expr = f"|{p(e)}×{p(f)}-{p(g)}|"
    part2_val = abs(e * f - g)
    op = random.choice(['+', '-'])
    final_expr = f"{part1_expr}{op}{part2_expr}"
    if op == '+':
        final_ans = part1_val + part2_val
    else:
        final_ans = part1_val - part2_val
    return {
        'question_text': f"計算 {final_expr} 的值。",
        'answer': '',
        'correct_answer': str(final_ans),
        'mode': 1
    }

def check(user_answer, correct_answer):
    is_correct = str(user_answer).strip() == str(correct_answer).strip()
    return {
        'correct': is_correct,
        'result': '正確' if is_correct else '錯誤'
    }