def generate():
    import random
    k = random.randint(1, 10)
    r = random.randint(2, 20)
    num = random.randint(1, 10)
    denom = random.randint(1, 10)
    vars_dict = df.get_safe_vars_for_pattern('p2h_frac_mult_rad', 'easy')
    vars_dict = {'k': k, 'r': r, 'num': num, 'denom': denom}
    latex_answer, steps = df.solve_problem_pattern('p2h_frac_mult_rad', vars_dict, 'easy')
    question_text = df.format_question_LaTeX('p2h_frac_mult_rad', vars_dict)  # [AST Fix: 安全初始化防護]
    return {'question_text': question_text, 'correct_answer': latex_answer, 'steps': steps}

def check(user_answer, correct_answer):
    return user_answer == correct_answer