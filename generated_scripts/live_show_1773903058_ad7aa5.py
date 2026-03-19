from core.domain_functions import DomainFunctionHelper
import re
df = DomainFunctionHelper()

def generate(level=1, **kwargs):
    pattern_id = 'p5b_conjugate_rad'
    difficulty = 'mid'
    term_count = 2
    radical_style = 'simplified'
    vars = df.get_safe_vars_for_pattern(pattern_id, difficulty, term_count=term_count, style=locals().get('radical_style', 'mixed'))
    ans, sol = df.solve_problem_pattern(pattern_id, vars, difficulty)
    question_text = df.format_question_LaTeX(pattern_id, vars)  # [AST Fix: 安全初始化防護]
    return {'question_text': question_text, 'answer': '', 'correct_answer': ans, 'solution_steps': sol, 'mode': 1, '_o1_healed': False}

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    question_text = locals().get('question_text', locals().get('text', ''))  # [AST Fix: 安全初始化防護]
    if not question_text:
        _t = [str(v) for k, v in locals().items() if re.match('^t\\d+$', k)]
        question_text = f'化簡 ${''.join(_t)}$' if _t else '計算 $0$ 的值。'  # [AST Fix: 安全初始化防護]
    correct_answer = locals().get('correct_answer', '')
    if correct_answer:
        correct_answer = str(correct_answer).replace('-', '-').replace('-', '-').replace('1\\sqrt', '\\sqrt')
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}