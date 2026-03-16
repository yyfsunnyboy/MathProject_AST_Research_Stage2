python

def generate():
    import random
    k = random.randint(1, 5)
    r = random.choice([2, 3, 5, 7, 11, 13, 17, 19])
    num = random.randint(1, 9)
    denom = random.randint(2, 9)
    while denom == 1:
        denom = random.randint(2, 9)
    vars_dict = df.get_safe_vars_for_pattern('p2h_frac_mult_rad', 'easy', term_count=2)
    question_text = df.format_question_LaTeX('p2h_frac_mult_rad', vars_dict)  # [AST Fix: 安全初始化防護]
    answer, steps = df.solve_problem_pattern('p2h_frac_mult_rad', vars_dict, 'easy')
    return {'question_text': question_text, 'correct_answer': answer, 'steps': steps}

def check(user_answer, correct_answer):
    return user_answer == correct_answer
if __name__ == '__main__':
    result = generate()
    print('Question:', result['question_text'])
    print('Answer:', result['correct_answer'])
    print('Steps:', result['steps'])