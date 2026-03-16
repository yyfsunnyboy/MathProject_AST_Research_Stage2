def generate():
    from random import randint
    pattern_id = 'p2h_frac_mult_rad'
    term_count = 1
    vars_dict = df.get_safe_vars_for_pattern(pattern_id, 'easy', term_count=term_count)
    latex_answer, steps = df.solve_problem_pattern(pattern_id, vars_dict, 'easy')
    question_text = df.format_question_LaTeX(pattern_id, vars_dict)  # [AST Fix: 安全初始化防護]
    return {'question_text': question_text, 'correct_answer': latex_answer, 'steps': steps}

def check(user_answer, correct_answer):
    return user_answer.strip() == correct_answer.strip()