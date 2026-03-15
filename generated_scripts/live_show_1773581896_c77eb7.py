import df

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}

def generate():
    pattern_id = 'p2a_mult_direct'
    difficulty = 'mid'
    vars = df.get_safe_vars_for_pattern(pattern_id, difficulty)
    ans, sol = df.solve_problem_pattern(pattern_id, vars, difficulty)
    question_text = df.format_question_LaTeX(pattern_id, vars)
    return {'question_text': question_text, 'answer': '', 'correct_answer': ans, 'solution_steps': sol, 'mode': 1, '_o1_healed': False}