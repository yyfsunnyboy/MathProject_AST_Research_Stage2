import random

def generate(level=1, **kwargs):
    c_val = random.randint(-10, 10)
    if c_val == 0: c_val = 1
    res_div = random.randint(-10, 10)
    target_sum = c_val * res_div
    a = random.randint(-50, 50)
    b = target_sum - a
    d = random.randint(-10, 10)
    e = random.randint(-10, 10)
    f = random.randint(-10, 10)
    g = random.randint(-50, 50)
    op = random.choice(['+', '-'])
    term1 = res_div * d
    term2 = abs(e * f + g)
    if op == '+':
        res = term1 + term2
    else:
        res = term1 - term2
    def p(n):
        return f"({n})" if n < 0 else str(n)
    def p_sign(n):
        return f"+({n})" if n < 0 else f"+{n}"
    expr_part1 = f"[({p(a)}){p_sign(b)}]÷{p(c_val)}×{p(d)}"
    g_op = '+' if g >= 0 else '-'
    expr_part2 = f"|{p(e)}×{p(f)}{g_op}{abs(g)}|"
    question = f"{expr_part1}{op}{expr_part2}"
    return {
        'question_text': f"計算 {question} 的值。",
        'answer': '',
        'correct_answer': str(res),
        'mode': 1
    }

def check(user_answer, correct_answer):
    is_correct = str(user_answer).strip() == str(correct_answer).strip()
    return {
        'correct': is_correct,
        'result': '正確' if is_correct else '錯誤'
    }