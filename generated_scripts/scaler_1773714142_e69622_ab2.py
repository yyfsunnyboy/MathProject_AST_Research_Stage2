pattern_id = "p1"  # 這行會被攔截器刪除，但為測試目的保留

# 由於題型為：分數根式 × 負分數根式
# 且目標題型為：\frac{\sqrt{5}}{2} \times (-\frac{\sqrt{2}}{5})
# 我們需生成同構題型：\frac{\sqrt{a}}{b} \times (-\frac{\sqrt{c}}{d})

import random
import sympy as sp

def generate(level=1, **kwargs):
    r1 = random.choice([2, 3, 5, 7])  # 第一個根號內數字
    den1 = random.choice([2, 3, 5, 8])  # 第一個分母
    r2 = random.choice([2, 3, 5, 7])  # 第二個根號內數字
    den2 = random.choice([3, 5, 7, 10])  # 第二個分母

    # 在 Python f-string 中，LaTeX 的大括號必須寫成 {{ }} 才能正確跳脫
    question_text = f"\\frac{{\\sqrt{{{r1}}}}}{{{den1}}} \\times \\left(-\\frac{{\\sqrt{{{r2}}}}}{{{den2}}}\\right)"
    expr = (sp.Rational(1, den1) * sp.sqrt(r1)) * (-sp.Rational(1, den2) * sp.sqrt(r2))
    ans_latex = sp.latex(sp.simplify(expr))

    return {
        'question_text': question_text,
        'correct_answer': ans_latex,
        'solution_steps': ["將兩個分數相乘，根號內數字相乘並化簡。"],
        'mode': 1
    }

def check(user_answer, correct_answer):
    return {'correct': str(user_answer).strip() == str(correct_answer).strip(), 'result': '正確'}