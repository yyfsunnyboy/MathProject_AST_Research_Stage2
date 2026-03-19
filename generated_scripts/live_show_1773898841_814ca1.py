from core.domain_functions import DomainFunctionHelper
import re
df = DomainFunctionHelper()

def generate(level=1, **kwargs):
    pattern_id = 'p2b_mult_distrib'
    difficulty = 'mid'
    term_count = 2
    radical_style = 'simplifiable'
    vars = df.get_safe_vars_for_pattern(pattern_id, difficulty, term_count=term_count, style=locals().get('radical_style', 'mixed'))
    ans, sol = df.solve_problem_pattern(pattern_id, vars, difficulty)
    question_text = df.format_question_LaTeX(pattern_id, vars)  # [AST Fix: 安全初始化防護]
    return {'question_text': question_text, 'answer': '', 'correct_answer': ans, 'solution_steps': sol, 'mode': 1, '_o1_healed': False}

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    question_text = locals().get('question_text', locals().get('text', ''))  # [AST Fix: 安全初始化防護]
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}