pattern_id = 'p2a_mult_direct'
difficulty = 'mid'
term_count = 2

def check(user_answer, correct_answer):
    try:
        return {'correct': str(user_answer).strip() == str(correct_answer).strip(), 'result': '自動補全比對'}
    except:
        return {'correct': False, 'result': '錯誤'}

def generate(level=1, **kwargs):
    try:
        from core.domain_functions import DomainFunctionHelper
        _df = DomainFunctionHelper()
        _pid = 'p1_add_sub'
        _diff = 'mid'
        _v = _df.get_safe_vars_for_pattern(_pid, _diff)
        _ans, _sol = _df.solve_problem_pattern(_pid, _v, _diff)
        _qt = _df.format_question_LaTeX(_pid, _v)
        return {'question_text': _qt, 'answer': '', 'correct_answer': _ans, 'solution_steps': _sol, 'mode': 1, '_o1_healed': False}
    except Exception:
        return {'question_text': 'Fallback due to severe hallucination', 'correct_answer': '\\text{Failed}'}