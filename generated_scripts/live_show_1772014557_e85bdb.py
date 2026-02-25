def generate(**kwargs):
    v1 = random.randint(-15, -2)
    v2 = random.randint(2, 10)
    v3 = random.randint(-15, -2)
    v4 = random.randint(2, 10)
    v5 = random.randint(1, 15)
    while v3 * v4 - v5 == 0:
        v5 = random.randint(1, 15)
    ans = v1 * v2 + abs(v3 * v4 - v5)
    question_text = f'計算 $$ {v1} \\times {v2} + \\left| {v3} \\times {v4} - {v5} \\right| $$ 的值。'  # [AST Fix: 安全初始化防護]
    correct_answer = str(ans)
    return {'question_text': question_text, 'answer': '', 'correct_answer': correct_answer, 'mode': 1}

def check(user_answer, correct_answer):
    correct = str(user_answer).strip().replace(' ', '') == str(correct_answer).strip().replace(' ', '')
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}