from core.domain_functions import DomainFunctionHelper
df = DomainFunctionHelper()

def generate(level=1, **kwargs):
    # [辨識1] Pattern ID: p4_frac_mult
    # [辨識2] Difficulty: mid
    # [辨識3] 辨識依據: 題目為分數乘除根式結構，含三項分數與根式運算
    # [辨識4] Term Count: 3

    pattern_id = "p4_frac_mult"
    difficulty  = "mid"
    term_count = 3

    # 以下為固定 scaffold，禁止修改
    vars = df.get_safe_vars_for_pattern(pattern_id, difficulty, term_count=term_count)
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