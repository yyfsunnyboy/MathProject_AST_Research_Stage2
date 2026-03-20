from core.domain_functions import DomainFunctionHelper
df = DomainFunctionHelper()

def generate(level=1, **kwargs):
    # [Pre-injected by Architect — model provided decisions below]
    pattern_id = "p3a_div_expr"
    difficulty = "mid"
    term_count = 2
    required_radical_style = "fraction_radical"
    # [Auto-appended scaffold — deterministic, DO NOT output]
    _req_rs = locals().get('required_radical_style')
    _retry_rs = bool(locals().get('_radical_style_retry', False))
    _base_rs = locals().get('radical_style', 'mixed')
    if _req_rs == 'simple_radical':
        _gen_style = 'simplified'
    else:
        _gen_style = _base_rs
    vars = df.get_safe_vars_for_pattern(
        pattern_id, difficulty, term_count=term_count,
        style=_gen_style, style_profile=_req_rs, style_retry_pass=_retry_rs,
    )
    ans, sol = df.solve_problem_pattern(pattern_id, vars, difficulty)
    question_text = df.format_question_LaTeX(pattern_id, vars)

    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': ans,
        'solution_steps': sol,
        'mode': 1,
        '_o1_healed': False
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}