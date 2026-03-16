def generate():
    import random
    vars = df.get_safe_vars_for_pattern('p2f_int_mult_rad', 'easy', term_count=1)
    latex_answer, steps = df.solve_problem_pattern('p2f_int_mult_rad', vars, 'easy')
    question_text = df.format_question_LaTeX('p2f_int_mult_rad', vars)  # [AST Fix: 安全初始化防護]

    def check(user_answer):
        return user_answer == latex_answer
    return {'question_text': question_text, 'correct_answer': latex_answer, 'steps': steps, 'check': check}
result = generate()
question_text = result['question_text']  # [AST Fix: 安全初始化防護]
correct_answer = result['correct_answer']
steps = result['steps']
print(f'Question: {question_text}')
print(f'Correct Answer: {correct_answer}')
print(f'Steps: {steps}')
print(f'Check Function: {check}')