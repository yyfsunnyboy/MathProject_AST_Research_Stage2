import random

def generate():
    pattern_id = 'p2g_rad_mult_frac'
    difficulty = 'easy'
    term_count = 1
    vars_dict = df.get_safe_vars_for_pattern(pattern_id, difficulty, term_count=term_count)
    k = vars_dict['k']
    r = vars_dict['r']
    num = vars_dict['num']
    den = vars_dict['den']
    question_text = f'{k}\\sqrt{{{r}}} \\times \\frac{{{num}}}{{{den}}}'  # [AST Fix: 安全初始化防護]
    expr = k * sqrt(r) * (num / den)
    correct_answer = f'{simplify(expr)}'
    steps = [f'原式 = {k}\\sqrt{{{r}}} \\times \\frac{{{num}}}{{{den}}}', f'= {k} \\times \\frac{{{num}}}{{{den}}} \\times \\sqrt{{{r}}}', f'= \\frac{{{k * num}}}{{{den}}} \\sqrt{{{r}}}', f'= {correct_answer}']
    return {'question_text': question_text, 'correct_answer': correct_answer, 'steps': steps}

def check(user_answer, correct_answer):
    try:
        user_val = simplify(user_answer)
        correct_val = simplify(correct_answer)
        return user_val == correct_val
    except:
        return False
if __name__ == '__main__':
    result = generate()
    print('題目:', result['question_text'])
    print('正確答案:', result['correct_answer'])
    print('解題步驟:')
    for step in result['steps']:
        print(step)